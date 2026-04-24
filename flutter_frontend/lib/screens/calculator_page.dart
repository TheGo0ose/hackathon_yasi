import 'dart:math';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/cut_corners.dart';

class CalculatorPage extends StatefulWidget {
  const CalculatorPage({super.key});

  @override
  State<CalculatorPage> createState() => _CalculatorPageState();
}

class _CalculatorPageState extends State<CalculatorPage> {
  final _amountCtrl = TextEditingController(text: '500000');
  final _termCtrl = TextEditingController(text: '36');
  final _rateCtrl = TextEditingController(text: '12.0');

  double _monthlyPayment = 16607.0;

  void _calculate() {
    double amt = double.tryParse(_amountCtrl.text) ?? 0;
    int term = int.tryParse(_termCtrl.text) ?? 1;
    if (term < 1) term = 1;
    double rate = double.tryParse(_rateCtrl.text) ?? 0;

    double p = (rate / 100) / 12;
    double payment = 0;
    if (p > 0) {
      payment = amt * (p * pow(1 + p, term)) / (pow(1 + p, term) - 1);
    } else {
      payment = amt / term;
    }

    setState(() {
      _monthlyPayment = payment;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent, // Let global smoke show
      appBar: AppBar(
        title: Text('CREDIT CALCULATOR', style: Theme.of(context).textTheme.labelLarge),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 800),
            child: ClipPath(
              clipper: CutCornerClipper(cutSize: 32, topLeft: true, bottomRight: true),
              child: Container(
                color: AppTheme.peachAccent.withOpacity(0.9),
                padding: const EdgeInsets.all(48.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Text(
                      'Credit Calculator',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Estimate your monthly payments without impacting your RizzChecker score.',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: Colors.white70,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 48),
                    
                    Wrap(
                      spacing: 24,
                      runSpacing: 24,
                      alignment: WrapAlignment.center,
                      children: [
                        _buildInputField('Loan Amount (₽)', _amountCtrl),
                        _buildInputField('Term (Months)', _termCtrl),
                        _buildInputField('Interest Rate (%)', _rateCtrl),
                      ],
                    ),

                    const SizedBox(height: 48),
                    Text(
                      '\${_monthlyPayment.round()} ₽',
                      style: Theme.of(context).textTheme.displayMedium?.copyWith(
                        color: AppTheme.peachLight,
                      ),
                    ),
                    Text(
                      'ESTIMATED MONTHLY PAYMENT',
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: Colors.white70,
                        letterSpacing: 2.0,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInputField(String label, TextEditingController ctrl) {
    return SizedBox(
      width: 180,
      child: TextFormField(
        controller: ctrl,
        onChanged: (_) => _calculate(),
        style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
        keyboardType: TextInputType.number,
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Colors.white70),
          enabledBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.white30)),
          focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.white)),
        ),
      ),
    );
  }
}
