import 'dart:math';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/cut_corners.dart';
import 'ai_chat_page.dart';

class ResultPage extends StatelessWidget {
  final Map<String, dynamic> resultData;
  final Map<String, dynamic> requestData;

  const ResultPage({
    super.key,
    required this.resultData,
    required this.requestData,
  });

  @override
  Widget build(BuildContext context) {
    // Parse probability
    final double probability = (resultData['probability_of_default'] as num).toDouble();
    final int score = resultData['credit_score'];
    final Map<String, dynamic> riskSegment = resultData['risk_segment'];
    
    // Parse color from hex "#22C55E" -> Color(0xFF22C55E)
    Color riskColor = Colors.grey;
    if (riskSegment['color'] != null) {
      String hex = (riskSegment['color'] as String).replaceAll('#', 'FF');
      riskColor = Color(int.parse(hex, radix: 16));
    }

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppTheme.peachLight),
        title: Text('SCORING RESULT', style: Theme.of(context).textTheme.labelLarge),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 40.0),
          child: Center(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(
                  'НАШИ РАСЧЁТЫ:',
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: AppTheme.textDim,
                    letterSpacing: 4.0,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'ПОКАЗАТЕЛЬ ДЕФОЛТА',
                  style: Theme.of(context).textTheme.displayMedium?.copyWith(
                    fontSize: 48,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 64),
                
                // Speedometer Indicator
                SizedBox(
                  width: 300,
                  height: 150,
                  child: CustomPaint(
                    painter: _SpeedometerPainter(
                      probability: probability,
                      activeColor: riskColor,
                    ),
                    child: Align(
                      alignment: Alignment.bottomCenter,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '$score',
                            style: Theme.of(context).textTheme.displayLarge?.copyWith(
                              color: riskColor,
                            ),
                          ),
                          Text(
                            'Кредитный балл',
                            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              color: AppTheme.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                
                const SizedBox(height: 32),
                Text(
                  riskSegment['description'] ?? '',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: AppTheme.peachLight,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  '${(probability * 100).toStringAsFixed(2)}% вероятность дефолта',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppTheme.textMuted),
                ),
                
                const SizedBox(height: 80),
                
                // Button to AI Analysis
                CutCornerButton(
                  text: 'Анализ и рекомендации ИИ',
                  backgroundColor: AppTheme.peachAccent,
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => AiChatPage(resultData: resultData, requestData: requestData),
                      ),
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
}

class _SpeedometerPainter extends CustomPainter {
  final double probability;
  final Color activeColor;

  _SpeedometerPainter({required this.probability, required this.activeColor});

  @override
  void paint(Canvas canvas, Size size) {
    // Draw arc from left (pi) to right (0) via top
    final double centerX = size.width / 2;
    final double centerY = size.height; // Bottom edge is center of circle
    final double radius = size.width / 2;
    final Rect rect = Rect.fromCircle(center: Offset(centerX, centerY), radius: radius);

    final bgPaint = Paint()
      ..color = AppTheme.border
      ..style = PaintingStyle.stroke
      ..strokeWidth = 24.0
      ..strokeCap = StrokeCap.round;

    final activePaint = Paint()
      ..color = activeColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 24.0
      ..strokeCap = StrokeCap.round;

    // Background arc (180 degrees)
    canvas.drawArc(rect, pi, pi, false, bgPaint);

    // Active arc (mapping probability [0, 1] -> [0, pi])
    // The angle from left to right is pi. 
    // Wait; if default probability is 0 -> left side. if 1 -> right side.
    final double sweepAngle = probability * pi;
    canvas.drawArc(rect, pi, sweepAngle, false, activePaint);
  }

  @override
  bool shouldRepaint(covariant _SpeedometerPainter oldDelegate) {
    return oldDelegate.probability != probability || oldDelegate.activeColor != activeColor;
  }
}
