import 'dart:math';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/cut_corners.dart';
import 'form_page.dart';

class CalculatorPage extends StatefulWidget {
  const CalculatorPage({super.key});

  @override
  State<CalculatorPage> createState() => _CalculatorPageState();
}

class _CalculatorPageState extends State<CalculatorPage> {
  final _amountCtrl = TextEditingController(text: '500000');
  final _termCtrl = TextEditingController(text: '36');
  final _rateCtrl = TextEditingController(text: '12.0');
  final _incomeCtrl = TextEditingController(text: '80000');

  bool _isAnnuity = true; // true = annuity, false = differentiated

  double _monthlyPayment = 0;
  double _totalPayment = 0;
  double _overpayment = 0;
  double _dti = 0;
  double _loanAmount = 500000;

  @override
  void initState() {
    super.initState();
    _calculate();
  }

  void _calculate() {
    double amt = double.tryParse(_amountCtrl.text) ?? 0;
    int term = int.tryParse(_termCtrl.text) ?? 1;
    if (term < 1) term = 1;
    double rate = double.tryParse(_rateCtrl.text) ?? 0;
    double income = double.tryParse(_incomeCtrl.text) ?? 1;
    if (income < 1) income = 1;

    double monthly;
    double total;

    if (_isAnnuity) {
      // Annuity formula
      double p = (rate / 100) / 12;
      if (p > 0) {
        monthly = amt * (p * pow(1 + p, term)) / (pow(1 + p, term) - 1);
      } else {
        monthly = amt / term;
      }
      total = monthly * term;
    } else {
      // Differentiated: first month payment (maximum)
      double principalPart = amt / term;
      double p = (rate / 100) / 12;
      monthly = principalPart + amt * p; // First (max) payment
      // Total = sum of all payments
      total = 0;
      for (int i = 0; i < term; i++) {
        double remaining = amt - (principalPart * i);
        total += principalPart + remaining * p;
      }
    }

    setState(() {
      _loanAmount = amt;
      _monthlyPayment = monthly;
      _totalPayment = total;
      _overpayment = total - amt;
      _dti = income > 0 ? (monthly / income) * 100 : 0;
    });
  }

  Color _dtiColor() {
    if (_dti <= 30) return const Color(0xFF22C55E);
    if (_dti <= 50) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }

  String _dtiLabel() {
    if (_dti <= 30) return 'Комфортная нагрузка';
    if (_dti <= 50) return 'Повышенная нагрузка';
    return 'Критическая нагрузка';
  }

  String _formatMoney(double v) {
    if (v >= 1000000) return '${(v / 1000000).toStringAsFixed(1)}M ₽';
    if (v >= 1000) return '${(v / 1000).toStringAsFixed(0)}K ₽';
    return '${v.round()} ₽';
  }

  @override
  Widget build(BuildContext context) {
    final interestRatio = _totalPayment > 0 ? _overpayment / _totalPayment : 0.0;

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text('CREDIT CALCULATOR', style: Theme.of(context).textTheme.labelLarge),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 900),
            child: Column(
              children: [
                // ── Input Card ──
                ClipPath(
                  clipper: CutCornerClipper(cutSize: 32, topLeft: true, bottomRight: true),
                  child: Container(
                    color: AppTheme.peachAccent.withOpacity(0.9),
                    padding: const EdgeInsets.all(48.0),
                    child: Column(
                      children: [
                        Text(
                          'Credit Calculator',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: Colors.white,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Рассчитайте платежи и оцените кредитную нагрузку',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Colors.white70,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 32),

                        // Payment type toggle
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              _buildToggle('Аннуитет', _isAnnuity, () {
                                setState(() => _isAnnuity = true);
                                _calculate();
                              }),
                              _buildToggle('Дифференц.', !_isAnnuity, () {
                                setState(() => _isAnnuity = false);
                                _calculate();
                              }),
                            ],
                          ),
                        ),
                        const SizedBox(height: 32),

                        Wrap(
                          spacing: 24,
                          runSpacing: 24,
                          alignment: WrapAlignment.center,
                          children: [
                            _buildInputField('Сумма кредита (₽)', _amountCtrl, 200),
                            _buildInputField('Срок (мес.)', _termCtrl, 140),
                            _buildInputField('Ставка (%)', _rateCtrl, 140),
                            _buildInputField('Ваш доход (₽)', _incomeCtrl, 200),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 32),

                // ── Results Grid ──
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Left: Payment + Overpayment
                    Expanded(
                      child: Column(
                        children: [
                          _buildResultCard(
                            '${_monthlyPayment.round()} ₽',
                            _isAnnuity ? 'ЕЖЕМЕСЯЧНЫЙ ПЛАТЁЖ' : 'МАКС. ПЛАТЁЖ (1-й мес.)',
                            AppTheme.cream,
                          ),
                          const SizedBox(height: 16),
                          _buildResultCard(
                            '${_overpayment.round()} ₽',
                            'ПЕРЕПЛАТА ЗА ВЕСЬ СРОК',
                            const Color(0xFFF59E0B),
                          ),
                          const SizedBox(height: 16),
                          _buildResultCard(
                            _formatMoney(_totalPayment),
                            'ИТОГО К ВОЗВРАТУ',
                            AppTheme.peachLight,
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(width: 24),

                    // Right: DTI + Breakdown
                    Expanded(
                      child: Column(
                        children: [
                          // DTI Gauge
                          _buildDtiCard(context),
                          const SizedBox(height: 16),
                          // Principal vs Interest breakdown
                          _buildBreakdownCard(context, interestRatio),
                        ],
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 32),

                // ── CTA: Check scoring ──
                CutCornerButton(
                  text: 'ПРОВЕРИТЬ ШАНСЫ НА ОДОБРЕНИЕ →',
                  backgroundColor: AppTheme.peachAccent,
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const FormPage()),
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildToggle(String label, bool active, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        decoration: BoxDecoration(
          color: active ? Colors.white : Colors.transparent,
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: active ? AppTheme.peachAccent : Colors.white70,
            fontWeight: FontWeight.w700,
            fontSize: 14,
            letterSpacing: 1,
          ),
        ),
      ),
    );
  }

  Widget _buildResultCard(String value, String label, Color color) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        children: [
          Text(value,
              style: TextStyle(
                color: color,
                fontSize: 28,
                fontWeight: FontWeight.w700,
                fontFamily: 'monospace',
              )),
          const SizedBox(height: 6),
          Text(label,
              style: const TextStyle(color: AppTheme.textDim, fontSize: 11, letterSpacing: 1.5)),
        ],
      ),
    );
  }

  Widget _buildDtiCard(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        children: [
          const Text('DTI — ДОЛГОВАЯ НАГРУЗКА',
              style: TextStyle(color: AppTheme.textDim, fontSize: 11, letterSpacing: 1.5)),
          const SizedBox(height: 16),
          // DTI percentage
          Text(
            '${_dti.toStringAsFixed(1)}%',
            style: TextStyle(
              color: _dtiColor(),
              fontSize: 42,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _dtiLabel(),
            style: TextStyle(color: _dtiColor(), fontSize: 14, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 16),
          // DTI bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (_dti / 100).clamp(0.0, 1.0),
              minHeight: 8,
              backgroundColor: AppTheme.border,
              valueColor: AlwaysStoppedAnimation<Color>(_dtiColor()),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('0%', style: TextStyle(color: AppTheme.textDim, fontSize: 10)),
              Text('30%', style: TextStyle(color: const Color(0xFF22C55E).withOpacity(0.5), fontSize: 10)),
              Text('50%', style: TextStyle(color: const Color(0xFFF59E0B).withOpacity(0.5), fontSize: 10)),
              Text('100%', style: TextStyle(color: const Color(0xFFEF4444).withOpacity(0.5), fontSize: 10)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBreakdownCard(BuildContext context, double interestRatio) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        children: [
          const Text('СТРУКТУРА ВЫПЛАТ',
              style: TextStyle(color: AppTheme.textDim, fontSize: 11, letterSpacing: 1.5)),
          const SizedBox(height: 16),
          // Stacked bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: SizedBox(
              height: 32,
              child: Row(
                children: [
                  Expanded(
                    flex: ((1 - interestRatio) * 100).round().clamp(1, 99),
                    child: Container(color: const Color(0xFF22C55E)),
                  ),
                  Expanded(
                    flex: (interestRatio * 100).round().clamp(1, 99),
                    child: Container(color: const Color(0xFFF59E0B)),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(width: 12, height: 12, color: const Color(0xFF22C55E)),
                  const SizedBox(width: 8),
                  Text(
                    'Тело: ${_formatMoney(_loanAmount)}',
                    style: const TextStyle(color: AppTheme.cream, fontSize: 13),
                  ),
                ],
              ),
              Row(
                children: [
                  Container(width: 12, height: 12, color: const Color(0xFFF59E0B)),
                  const SizedBox(width: 8),
                  Text(
                    'Проценты: ${_formatMoney(_overpayment)}',
                    style: const TextStyle(color: AppTheme.cream, fontSize: 13),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInputField(String label, TextEditingController ctrl, double width) {
    return SizedBox(
      width: width,
      child: TextFormField(
        controller: ctrl,
        onChanged: (_) => _calculate(),
        style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Colors.white70, fontSize: 12),
          enabledBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.white30)),
          focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.white)),
        ),
      ),
    );
  }
}
