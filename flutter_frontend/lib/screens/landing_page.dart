import 'package:flutter/material.dart';
import '../widgets/cut_corners.dart';
import '../theme/app_theme.dart';
import 'calculator_page.dart';
import 'import_page.dart';
import 'form_page.dart';
import 'ai_chat_page.dart';

class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
            const _NavBar(),
            Expanded(
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 40.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Massive Bold Title
                      Text(
                        'Next-Gen',
                        style: Theme.of(context).textTheme.displayMedium,
                        textAlign: TextAlign.center,
                      ),
                      Text(
                        'AI Scoring',
                        style: Theme.of(context).textTheme.displayLarge?.copyWith(
                          fontStyle: FontStyle.italic,
                          color: AppTheme.cream,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 32),
                      
                      // Subtitle
                      Text(
                        'for Unmatched Creative Freedom & Human-\nCentered AI Experiences',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontFamily: 'monospace',
                          fontSize: 14,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 64),
                      
                      // Cut Corner Button
                      CutCornerButton(
                        text: 'Start Scoring',
                        onTap: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => const FormPage()),
                          );
                        },
                      ),
                      
                      const SizedBox(height: 100),
                      Text(
                        'Almost there, stay tuned!',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontFamily: 'monospace',
                          fontSize: 12,
                          color: AppTheme.textDim,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      );
  }
}

class _NavBar extends StatelessWidget {
  const _NavBar();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40.0, vertical: 32.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const Icon(Icons.blur_linear, color: AppTheme.cream, size: 28),
              const SizedBox(width: 12),
              Text(
                'RIZZCHECKER',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontSize: 20,
                  letterSpacing: 2.0,
                ),
              ),
            ],
          ),
          Row(
            children: [
              _NavTextRef('CREDIT CALCULATOR', onTap: () {
                 Navigator.push(context, MaterialPageRoute(builder: (_) => const CalculatorPage()));
              }),
              const SizedBox(width: 24),
              _NavTextRef('IMPORT DATA', onTap: () {
                 Navigator.push(context, MaterialPageRoute(builder: (_) => const ImportPage()));
              }),
              const SizedBox(width: 24),
              _NavTextRef('AI ADVISOR', color: AppTheme.cream, onTap: () {
                 Navigator.push(context, MaterialPageRoute(builder: (_) => const AiChatPage()));
              }),
            ],
          )
        ],
      ),
    );
  }
}

class _NavTextRef extends StatelessWidget {
  final String text;
  final Color color;
  final VoidCallback? onTap;
  const _NavTextRef(this.text, {this.color = AppTheme.textMuted, this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Text(
        text,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
          color: color,
          fontSize: 12,
          letterSpacing: 2.0,
        ),
      ),
    );
  }
}
