import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:csv/csv.dart';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../theme/app_theme.dart';
import '../widgets/cut_corners.dart';

class ImportPage extends StatefulWidget {
  const ImportPage({super.key});

  @override
  State<ImportPage> createState() => _ImportPageState();
}

class _ImportPageState extends State<ImportPage> {


  bool _isLoading = false;
  String? _fileName;
  int _totalRows = 0;
  int _approved = 0;
  int _declined = 0;
  List<Map<String, dynamic>> _results = [];

  // Expected CSV columns
  static const _requiredColumns = [
    'age', 'monthly_income', 'employment_years', 'loan_amount',
    'loan_term_months', 'interest_rate', 'past_due_30d', 'inquiries_6m',
  ];

  Future<void> _pickAndProcess() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;

    final file = result.files.first;
    if (file.bytes == null) return;

    setState(() {
      _isLoading = true;
      _fileName = file.name;
      _results = [];
    });

    try {
      // Parse CSV
      final csvString = utf8.decode(file.bytes!);
      final rows = const CsvToListConverter(eol: '\n').convert(csvString);
      if (rows.length < 2) {
        _showError('CSV файл пустой или содержит только заголовки.');
        return;
      }

      // Map headers
      final headers = rows.first.map((h) => h.toString().trim().toLowerCase()).toList();

      // Find column indices
      final Map<String, int> colIndex = {};
      for (var col in _requiredColumns) {
        final idx = headers.indexOf(col);
        if (idx == -1) {
          _showError('Не найден столбец: $col\n\nОжидаемые столбцы: ${_requiredColumns.join(", ")}');
          return;
        }
        colIndex[col] = idx;
      }

      // Build request bodies
      final List<Map<String, dynamic>> requestBodies = [];
      for (int i = 1; i < rows.length; i++) {
        final row = rows[i];
        if (row.length < headers.length) continue;
        try {
          requestBodies.add({
            'age': int.parse(row[colIndex['age']!].toString().trim()),
            'monthly_income': double.parse(row[colIndex['monthly_income']!].toString().trim()),
            'employment_years': double.parse(row[colIndex['employment_years']!].toString().trim()),
            'loan_amount': double.parse(row[colIndex['loan_amount']!].toString().trim()),
            'loan_term_months': int.parse(row[colIndex['loan_term_months']!].toString().trim().split('.').first),
            'interest_rate': double.parse(row[colIndex['interest_rate']!].toString().trim()),
            'past_due_30d': int.parse(row[colIndex['past_due_30d']!].toString().trim().split('.').first),
            'inquiries_6m': int.parse(row[colIndex['inquiries_6m']!].toString().trim().split('.').first),
          });
        } catch (_) {
          // Skip malformed rows
        }
      }

      if (requestBodies.isEmpty) {
        _showError('Не удалось распарсить ни одной строки.');
        return;
      }

      // Call batch endpoint
      final response = await http.post(
        Uri.parse('$backendUrl/api/v1/scoring/batch'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(requestBodies),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        int approved = 0;
        int declined = 0;
        final List<Map<String, dynamic>> combined = [];

        for (int i = 0; i < data.length; i++) {
          final res = data[i] as Map<String, dynamic>;
          if (res['decision'] == 'APPROVED') approved++;
          else declined++;

          combined.add({
            'index': i + 1,
            'age': requestBodies[i]['age'],
            'income': requestBodies[i]['monthly_income'],
            'loan': requestBodies[i]['loan_amount'],
            'decision': res['decision'],
            'score': res['credit_score'],
            'probability': res['probability_of_default'],
            'risk': res['risk_segment']?['label'] ?? '',
          });
        }

        setState(() {
          _totalRows = data.length;
          _approved = approved;
          _declined = declined;
          _results = combined;
        });
      } else {
        _showError('Ошибка сервера: ${response.statusCode}');
      }
    } catch (e) {
      _showError('Ошибка: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String text) {
    setState(() => _isLoading = false);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      backgroundColor: Colors.redAccent,
      content: Text(text),
      duration: const Duration(seconds: 4),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppTheme.peachLight),
        title: Text('IMPORT DATA', style: Theme.of(context).textTheme.labelLarge),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 900),
            child: Column(
              children: [
                // Upload section
                _buildUploadCard(context),
                if (_results.isNotEmpty) ...[
                  const SizedBox(height: 32),
                  _buildStatsRow(context),
                  const SizedBox(height: 24),
                  _buildResultsTable(context),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildUploadCard(BuildContext context) {
    return ClipPath(
      clipper: CutCornerClipper(cutSize: 24, topLeft: true, bottomRight: true),
      child: Container(
        color: AppTheme.surface,
        padding: const EdgeInsets.all(48.0),
        child: Column(
          children: [
            const Icon(Icons.upload_file, size: 48, color: AppTheme.peachAccent),
            const SizedBox(height: 16),
            Text(
              'Загрузите CSV файл',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(color: AppTheme.cream),
            ),
            const SizedBox(height: 8),
            Text(
              'Столбцы: age, monthly_income, employment_years, loan_amount,\nloan_term_months, interest_rate, past_due_30d, inquiries_6m',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.textDim),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            if (_isLoading)
              const CircularProgressIndicator(color: AppTheme.peachAccent)
            else
              CutCornerButton(
                text: _fileName != null ? 'ЗАГРУЗИТЬ ДРУГОЙ' : 'ВЫБРАТЬ CSV',
                onTap: _pickAndProcess,
              ),
            if (_fileName != null) ...[
              const SizedBox(height: 12),
              Text(
                _fileName!,
                style: const TextStyle(color: AppTheme.textMuted, fontSize: 13),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildStatsRow(BuildContext context) {
    return Row(
      children: [
        _buildStatCard(context, '$_totalRows', 'Всего', AppTheme.cream),
        const SizedBox(width: 16),
        _buildStatCard(context, '$_approved', 'Одобрено', const Color(0xFF22C55E)),
        const SizedBox(width: 16),
        _buildStatCard(context, '$_declined', 'Отказано', const Color(0xFFEF4444)),
        const SizedBox(width: 16),
        _buildStatCard(
          context,
          _totalRows > 0 ? '${(_approved / _totalRows * 100).toStringAsFixed(1)}%' : '—',
          'Approval Rate',
          AppTheme.peachAccent,
        ),
      ],
    );
  }

  Widget _buildStatCard(BuildContext context, String value, String label, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: AppTheme.border),
        ),
        child: Column(
          children: [
            Text(value,
                style: Theme.of(context)
                    .textTheme
                    .headlineMedium
                    ?.copyWith(color: color, fontWeight: FontWeight.w700)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(color: AppTheme.textDim, fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildResultsTable(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: AppTheme.border),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          headingRowColor: WidgetStateProperty.all(AppTheme.bg2),
          dataRowColor: WidgetStateProperty.all(Colors.transparent),
          columns: const [
            DataColumn(label: Text('#', style: TextStyle(color: AppTheme.textDim))),
            DataColumn(label: Text('Age', style: TextStyle(color: AppTheme.textDim))),
            DataColumn(label: Text('Income', style: TextStyle(color: AppTheme.textDim))),
            DataColumn(label: Text('Loan', style: TextStyle(color: AppTheme.textDim))),
            DataColumn(label: Text('Score', style: TextStyle(color: AppTheme.textDim))),
            DataColumn(label: Text('P(def)', style: TextStyle(color: AppTheme.textDim))),
            DataColumn(label: Text('Risk', style: TextStyle(color: AppTheme.textDim))),
            DataColumn(label: Text('Decision', style: TextStyle(color: AppTheme.textDim))),
          ],
          rows: _results.map((r) {
            final isApproved = r['decision'] == 'APPROVED';
            return DataRow(cells: [
              DataCell(Text('${r['index']}', style: const TextStyle(color: AppTheme.cream))),
              DataCell(Text('${r['age']}', style: const TextStyle(color: AppTheme.cream))),
              DataCell(Text('${(r['income'] as num).round()}', style: const TextStyle(color: AppTheme.cream))),
              DataCell(Text('${(r['loan'] as num).round()}', style: const TextStyle(color: AppTheme.cream))),
              DataCell(Text('${r['score']}', style: const TextStyle(color: AppTheme.cream))),
              DataCell(Text('${((r['probability'] as num) * 100).toStringAsFixed(1)}%',
                  style: const TextStyle(color: AppTheme.cream))),
              DataCell(Text('${r['risk']}', style: TextStyle(
                color: r['risk'] == 'low' ? const Color(0xFF22C55E)
                     : r['risk'] == 'medium' ? const Color(0xFFF59E0B)
                     : const Color(0xFFEF4444),
              ))),
              DataCell(Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isApproved ? const Color(0xFF22C55E).withOpacity(0.15) : const Color(0xFFEF4444).withOpacity(0.15),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  isApproved ? '✓' : '✗',
                  style: TextStyle(
                    color: isApproved ? const Color(0xFF22C55E) : const Color(0xFFEF4444),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              )),
            ]);
          }).toList(),
        ),
      ),
    );
  }
}
