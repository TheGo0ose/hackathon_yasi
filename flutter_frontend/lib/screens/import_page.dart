import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/cut_corners.dart';

class ImportPage extends StatelessWidget {
  const ImportPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent, // Let global smoke show through
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppTheme.peachLight),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(
                'Import Existing Data',
                style: Theme.of(context).textTheme.displayMedium?.copyWith(
                  fontSize: 48,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              Text(
                'Connect your bank or upload your financial history.\nWe will analyze your accumulated data securely to calculate your default probability.',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  fontSize: 16,
                  color: AppTheme.textMuted,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 64),
              CutCornerButton(
                text: 'SECURE IMPORT',
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Importing data...'),
                  ));
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}
