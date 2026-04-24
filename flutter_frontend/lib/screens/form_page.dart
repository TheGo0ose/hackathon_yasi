import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../widgets/cut_corners.dart';
import '../theme/app_theme.dart';
import 'result_page.dart';

class FormPage extends StatefulWidget {
  const FormPage({super.key});

  @override
  State<FormPage> createState() => _FormPageState();
}

class _FormPageState extends State<FormPage> {
  final _formKey = GlobalKey<FormState>();
  
  // Controllers
  final _ageCtrl = TextEditingController(text: '29');
  final _incomeCtrl = TextEditingController(text: '320000');
  final _empYearsCtrl = TextEditingController(text: '3.5');
  final _loanAmtCtrl = TextEditingController(text: '650000');
  final _loanTermCtrl = TextEditingController(text: '48');
  final _interestRateCtrl = TextEditingController(text: '15.0');
  final _pastDueCtrl = TextEditingController(text: '0');
  final _inquiriesCtrl = TextEditingController(text: '1');

  bool _isLoading = false;

  Future<void> _submitScoring() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      final requestBody = {
        "age": int.parse(_ageCtrl.text),
        "monthly_income": double.parse(_incomeCtrl.text),
        "employment_years": double.parse(_empYearsCtrl.text),
        "loan_amount": double.parse(_loanAmtCtrl.text),
        "loan_term_months": int.parse(_loanTermCtrl.text),
        "interest_rate": double.parse(_interestRateCtrl.text),
        "past_due_30d": int.parse(_pastDueCtrl.text),
        "inquiries_6m": int.parse(_inquiriesCtrl.text)
      };

      final response = await http.post(
        Uri.parse('http://localhost:8000/api/v1/scoring/predict'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(requestBody),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ResultPage(resultData: data, requestData: requestBody),
            ),
          );
        }
      } else {
        _showError('Server Error: \${response.statusCode}');
      }
    } catch (e) {
      _showError('Connection failed. Make sure backend is running on 8000.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String text) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      backgroundColor: Colors.redAccent,
      content: Text(text),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bg2,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppTheme.peachLight),
        title: Text('SCORING DATA', style: Theme.of(context).textTheme.labelLarge),
        centerTitle: true,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 800),
            child: ClipPath(
              clipper: CutCornerClipper(cutSize: 32, topLeft: true, bottomRight: true),
              child: Container(
                color: AppTheme.peachAccent.withOpacity(0.9), // Bright red/peach as on screenshot
                padding: const EdgeInsets.all(48.0),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Hi, RizzChecker team.',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Please evaluate my credit risk profile for a loan request.',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: Colors.white70,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 32),
                      
                      // Grid of inputs
                      Wrap(
                         spacing: 24.0,
                         runSpacing: 24.0,
                         children: [
                            _buildInput('Age', _ageCtrl, width: 120),
                            _buildInput('Monthly Income', _incomeCtrl, width: 200),
                            _buildInput('Employment Years', _empYearsCtrl, width: 160),
                            _buildInput('Loan Amount', _loanAmtCtrl, width: 200),
                            _buildInput('Term (months)', _loanTermCtrl, width: 150),
                            _buildInput('Interest Rate %', _interestRateCtrl, width: 150),
                            _buildInput('Past Due 30d+', _pastDueCtrl, width: 150),
                            _buildInput('Inquiries 6M', _inquiriesCtrl, width: 150),
                         ],
                      ),
                      const SizedBox(height: 48),
                      
                      _isLoading 
                        ? const Center(child: CircularProgressIndicator(color: Colors.white))
                        : Container(
                            color: Colors.white,
                            child: TextButton(
                              onPressed: _submitScoring,
                              style: TextButton.styleFrom(
                                padding: const EdgeInsets.symmetric(vertical: 20),
                              ),
                              child: Text(
                                'CALCULATE RISK',
                                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                                  color: AppTheme.peachAccent,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 2.0,
                                ),
                              ),
                            ),
                          )
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInput(String label, TextEditingController ctrl, {double width = 150}) {
    return SizedBox(
      width: width,
      child: TextFormField(
        controller: ctrl,
        style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w700),
        cursorColor: Colors.white,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Colors.white70, fontSize: 12, letterSpacing: 1.0),
          enabledBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.white30)),
          focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.white)),
        ),
        validator: (value) => value!.isEmpty ? '*' : null,
      ),
    );
  }
}
