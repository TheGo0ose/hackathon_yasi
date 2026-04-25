import 'package:flutter/material.dart';
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
  final List<Map<String, String>> _messages = [];
  bool _isTyping = false;

  @override
  void initState() {
    super.initState();
    _analyzeData();
  }

  void _analyzeData() {
    if (widget.resultData == null || widget.resultData!['shap_values'] == null) {
      setState(() {
        _messages.add({
          'role': 'ai',
          'text': "Привет! Вы пока не заполняли форму скоринга. Можете задавать мне общие вопросы об улучшении кредитного потенциала.",
        });
      });
      return;
    }

    final shap = widget.resultData!['shap_values']['feature_contributions'] as Map<String, dynamic>;
    
    // Sort to find biggest negative impacts (increasing default risk)
    var entries = shap.entries.toList();
    entries.sort((a, b) => b.value.compareTo(a.value)); // Descending shape values
    
    String mainProblem = entries.isNotEmpty && entries.first.value > 0
        ? "Ваш показатель '\${entries.first.key}' сильнее всего увеличил риск."
        : "Вы выглядите очень надежным заемщиком.";

    setState(() {
      _messages.add({
        'role': 'ai',
        'text': "Привет! Я проанализировал вашу заявку.\n\n\$mainProblem\n\nМогу дать советы, как улучшить вашу кредитную привлекательность. Что бы вы хотели обсудить?",
      });
    });
  }

  void _sendMessage() {
    final txt = _msgCtrl.text.trim();
    if (txt.isEmpty) return;
    
    setState(() {
      _messages.add({'role': 'user', 'text': txt});
      _msgCtrl.clear();
      _isTyping = true;
    });

    // Mock AI delay responding
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          _isTyping = false;
          _messages.add({
            'role': 'ai',
            'text': "Для улучшения ситуации рекомендую закрыть неактивные кредитные карты и постараться уменьшить текущую долговую нагрузку. Также старайтесь не запрашивать кредитную историю слишком часто (inquiries).",
          });
        });
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
                child: Text('AI is thinking...', style: TextStyle(color: AppTheme.textDim, fontStyle: FontStyle.italic)),
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
                      hintText: 'Как мне снизить ставку?',
                      border: OutlineInputBorder(borderSide: BorderSide(color: AppTheme.peachAccent.withOpacity(0.5))),
                      enabledBorder: const OutlineInputBorder(borderSide: BorderSide(color: AppTheme.border)),
                      focusedBorder: const OutlineInputBorder(borderSide: BorderSide(color: AppTheme.peachAccent)),
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
}
