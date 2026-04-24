import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../theme/app_theme.dart';
import '../widgets/cut_corners.dart';

class AiChatPage extends StatefulWidget {
  final Map<String, dynamic>? resultData;
  final Map<String, dynamic>? requestData;

  const AiChatPage({
    super.key,
    this.resultData,
    this.requestData,
  });

  @override
  State<AiChatPage> createState() => _AiChatPageState();
}

class _AiChatPageState extends State<AiChatPage> {
  final TextEditingController _msgCtrl = TextEditingController();
  final ScrollController _scrollCtrl = ScrollController();
  final List<Map<String, String>> _messages = [];
  bool _isTyping = false;

  // Backend URL — same as form_page.dart

  @override
  void initState() {
    super.initState();
    _sendInitialGreeting();
  }

  /// Build ML context from scoring result for the advisor API
  Map<String, dynamic> _buildMlContext() {
    if (widget.resultData == null) {
      return {
        'has_scoring': false,
        'note': 'Пользователь ещё не проходил скоринг.',
      };
    }

    final result = widget.resultData!;
    final features = widget.requestData ?? {};
    final contributions =
        (result['shap_values']?['feature_contributions'] as Map<String, dynamic>?) ?? {};

    // Sort contributions descending
    final sortedContribs = contributions.entries.toList()
      ..sort((a, b) => (b.value as num).compareTo(a.value as num));

    const featureLabels = {
      'age': 'Возраст',
      'monthly_income': 'Ежемесячный доход',
      'employment_years': 'Стаж работы',
      'loan_amount': 'Сумма кредита',
      'loan_term_months': 'Срок кредита',
      'interest_rate': 'Процентная ставка',
      'past_due_30d': 'Просрочки 30+ дней',
      'inquiries_6m': 'Кредитные запросы за 6 мес.',
    };

    return {
      'has_scoring': true,
      'decision': result['decision'],
      'probability_of_default': result['probability_of_default'],
      'credit_score': result['credit_score'],
      'risk_segment': result['risk_segment']?['label'] ?? 'unknown',
      'threshold': result['threshold_used'],
      'features': {
        for (var e in features.entries) (featureLabels[e.key] ?? e.key): e.value,
      },
      'contributions': [
        for (var e in sortedContribs)
          {
            'feature': featureLabels[e.key] ?? e.key,
            'raw_feature_name': e.key,
            'value': features[e.key],
            'contribution': e.value,
            'direction': (e.value as num) > 0 ? 'увеличивает риск' : 'снижает риск',
          },
      ],
    };
  }

  /// Build chat history for the advisor API (role: user/assistant)
  List<Map<String, String>> _buildChatHistory() {
    return _messages
        .map((m) => {
              'role': m['role'] == 'user' ? 'user' : 'assistant',
              'content': m['text']!,
            })
        .toList();
  }

  /// Send initial greeting based on whether we have scoring data
  void _sendInitialGreeting() {
    if (widget.resultData == null || widget.resultData!['shap_values'] == null) {
      setState(() {
        _messages.add({
          'role': 'ai',
          'text':
              'Привет! 👋 Вы пока не заполняли форму скоринга. Можете задавать мне общие вопросы о кредитах, финансах и улучшении кредитного потенциала.',
        });
      });
      return;
    }

    // Analyze SHAP values for initial insight
    final shap =
        widget.resultData!['shap_values']['feature_contributions'] as Map<String, dynamic>;
    final entries = shap.entries.toList()
      ..sort((a, b) => (b.value as num).compareTo(a.value as num));

    final decision = widget.resultData!['decision'] ?? '';
    final score = widget.resultData!['credit_score'] ?? 0;

    String greeting;
    if (decision == 'APPROVED') {
      greeting =
          'Поздравляю! ✅ Ваша заявка одобрена (скор $score/850). Хотите узнать, как ещё улучшить условия или снизить ставку?';
    } else {
      final worst = entries.isNotEmpty && (entries.first.value as num) > 0
          ? entries.first.key
          : null;
      const labels = {
        'age': 'возраст',
        'monthly_income': 'уровень дохода',
        'employment_years': 'стаж работы',
        'loan_amount': 'сумма кредита',
        'loan_term_months': 'срок кредита',
        'interest_rate': 'процентная ставка',
        'past_due_30d': 'просрочки',
        'inquiries_6m': 'кредитные запросы',
      };
      final worstLabel = labels[worst] ?? worst ?? 'неизвестный фактор';
      greeting =
          'К сожалению, заявка отклонена (скор $score/850). Главный фактор риска — $worstLabel. Спросите меня, что конкретно нужно сделать для одобрения! 💡';
    }

    setState(() {
      _messages.add({'role': 'ai', 'text': greeting});
    });
  }

  /// Send message to the real advisor API
  Future<void> _sendMessage() async {
    final txt = _msgCtrl.text.trim();
    if (txt.isEmpty || _isTyping) return;

    setState(() {
      _messages.add({'role': 'user', 'text': txt});
      _msgCtrl.clear();
      _isTyping = true;
    });
    _scrollToBottom();

    try {
      final response = await http.post(
        Uri.parse('$backendUrl/api/v1/advisor/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'ml_context': _buildMlContext(),
          'chat_history': _buildChatHistory(),
          'user_message': txt,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (mounted) {
          setState(() {
            _isTyping = false;
            _messages.add({
              'role': 'ai',
              'text': data['reply'] ?? 'Нет ответа.',
            });
          });
        }
      } else {
        _addErrorMessage('Ошибка сервера: ${response.statusCode}');
      }
    } catch (e) {
      _addErrorMessage('Не удалось связаться с сервером. Убедитесь, что бэкенд запущен.');
    }

    _scrollToBottom();
  }

  void _addErrorMessage(String text) {
    if (mounted) {
      setState(() {
        _isTyping = false;
        _messages.add({'role': 'ai', 'text': '⚠️ $text'});
      });
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text('RIZZCHECKER ADVISOR', style: Theme.of(context).textTheme.labelLarge),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
      body: Column(
        children: [
          // Chat history
          Expanded(
            child: ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.all(24.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg['role'] == 'user';
                return _buildChatBubble(msg['text']!, isUser);
              },
            ),
          ),
          if (_isTyping)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 24, vertical: 8),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text('AI is thinking...',
                    style: TextStyle(color: AppTheme.textDim, fontStyle: FontStyle.italic)),
              ),
            ),
          // Input area
          Container(
            padding: const EdgeInsets.all(24.0),
            decoration: const BoxDecoration(
              color: AppTheme.bg2,
              border: Border(top: BorderSide(color: AppTheme.border)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _msgCtrl,
                    style: const TextStyle(color: Colors.white, fontSize: 16),
                    decoration: InputDecoration(
                      hintText: 'Как мне улучшить скор?',
                      hintStyle: TextStyle(color: Colors.white.withOpacity(0.3)),
                      border: OutlineInputBorder(
                          borderSide: BorderSide(color: AppTheme.peachAccent.withOpacity(0.5))),
                      enabledBorder:
                          const OutlineInputBorder(borderSide: BorderSide(color: AppTheme.border)),
                      focusedBorder:
                          const OutlineInputBorder(borderSide: BorderSide(color: AppTheme.peachAccent)),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 16),
                CutCornerButton(
                  text: 'SEND',
                  onTap: _sendMessage,
                )
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildChatBubble(String text, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16.0),
        padding: const EdgeInsets.all(16.0),
        constraints: const BoxConstraints(maxWidth: 400),
        decoration: BoxDecoration(
          color: isUser ? AppTheme.peachAccent.withOpacity(0.1) : AppTheme.surface,
          borderRadius: BorderRadius.circular(8.0),
          border: Border.all(color: isUser ? AppTheme.peachAccent.withOpacity(0.3) : AppTheme.border),
        ),
        child: Text(
          text,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: isUser ? AppTheme.peachLight : AppTheme.cream,
              ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _msgCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }
}
