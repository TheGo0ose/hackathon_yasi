import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/landing_page.dart';

void main() {
  runApp(const YasiApp());
}

class NavigationService {
  static final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();
}

class YasiApp extends StatelessWidget {
  const YasiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RizzChecker AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      navigatorKey: NavigationService.navigatorKey,
      home: const LandingPage(),
    );
  }
}
