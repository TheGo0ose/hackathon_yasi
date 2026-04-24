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
    final isNarrow = MediaQuery.of(context).size.width < 600;

    return Padding(
      padding: EdgeInsets.symmetric(
        horizontal: isNarrow ? 16.0 : 40.0,
        vertical: isNarrow ? 16.0 : 32.0,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Logo
          Row(
            children: [
              const Icon(Icons.blur_linear, color: AppTheme.cream, size: 28),
              const SizedBox(width: 12),
              Text(
                'RIZZCHECKER',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontSize: isNarrow ? 16 : 20,
                  letterSpacing: 2.0,
                ),
              ),
            ],
          ),
          // Desktop: inline links | Mobile: hamburger
          if (isNarrow)
            IconButton(
              icon: const Icon(Icons.menu, color: AppTheme.cream, size: 28),
              onPressed: () => _showMobileMenu(context),
            )
          else
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
            ),
        ],
      ),
    );
  }

  void _showMobileMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.bg2,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            Container(
              width: 40, height: 4,
              decoration: BoxDecoration(
                color: AppTheme.textDim,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 16),
            _MobileMenuItem(
              icon: Icons.calculate_outlined,
              label: 'Credit Calculator',
              onTap: () {
                Navigator.pop(ctx);
                Navigator.push(context, MaterialPageRoute(builder: (_) => const CalculatorPage()));
              },
            ),
            _MobileMenuItem(
              icon: Icons.upload_file_outlined,
              label: 'Import Data',
              onTap: () {
                Navigator.pop(ctx);
                Navigator.push(context, MaterialPageRoute(builder: (_) => const ImportPage()));
              },
            ),
            _MobileMenuItem(
              icon: Icons.smart_toy_outlined,
              label: 'AI Advisor',
              onTap: () {
                Navigator.pop(ctx);
                Navigator.push(context, MaterialPageRoute(builder: (_) => const AiChatPage()));
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _MobileMenuItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _MobileMenuItem({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppTheme.peachAccent),
      title: Text(label, style: const TextStyle(color: AppTheme.cream, fontSize: 16, letterSpacing: 1)),
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 24),
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

