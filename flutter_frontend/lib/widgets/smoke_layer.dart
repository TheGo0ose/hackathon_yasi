import 'dart:math';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class SmokeLayer extends StatefulWidget {
  final Widget child;
  const SmokeLayer({super.key, required this.child});

  @override
  State<SmokeLayer> createState() => _SmokeLayerState();
}

class _SmokeLayerState extends State<SmokeLayer> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  List<Particle> particles = [];
  Offset pointer = const Offset(500, 500);

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(seconds: 100))
      ..addListener(() {
        _updateParticles();
        setState(() {});
      })
      ..repeat();
      
    // Initialize initial particles
    for (int i = 0; i < 40; i++) {
      particles.add(Particle(
        x: Random().nextDouble() * 1000,
        y: Random().nextDouble() * 1000,
        vx: (Random().nextDouble() - 0.5) * 1.5,
        vy: (Random().nextDouble() - 0.5) * 1.5,
        radius: 40 + Random().nextDouble() * 100,
        alpha: 0.05 + Random().nextDouble() * 0.1,
      ));
    }
  }

  void _updateParticles() {
    final Size size = MediaQuery.of(context).size.isEmpty 
        ? const Size(1000, 1000) 
        : MediaQuery.of(context).size;
        
    for (var p in particles) {
      // Move
      p.x += p.vx;
      p.y += p.vy;

      // Mouse attraction / disturbance (flowing towards but swirling)
      double dx = pointer.dx - p.x;
      double dy = pointer.dy - p.y;
      double dist = sqrt(dx * dx + dy * dy);
      
      if (dist < 400.0) {
        // Aggressive attract / repulse to create tight glowing fluid follow
        p.vx += (dx / dist) * 0.8;
        p.vy += (dy / dist) * 0.8;
      }
      
      // Speed cap for trails
      double speed = sqrt(p.vx * p.vx + p.vy * p.vy);
      if (speed > 12.0) {
          p.vx = (p.vx / speed) * 12.0;
          p.vy = (p.vy / speed) * 12.0;
      }
      
      // Friction
      p.vx *= 0.95;
      p.vy *= 0.95;
      
      // Ambient random walk to keep it moving
      p.vx += (Random().nextDouble() - 0.5) * 0.1;
      p.vy += (Random().nextDouble() - 0.5) * 0.1;

      // Wrap around
      if (p.x < -200) p.x = size.width + 200;
      if (p.x > size.width + 200) p.x = -200;
      if (p.y < -200) p.y = size.height + 200;
      if (p.y > size.height + 200) p.y = -200;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onHover: (e) {
        pointer = e.position;
      },
      child: GestureDetector(
        onPanUpdate: (e) {
          pointer = e.globalPosition;
        },
        child: Stack(
          fit: StackFit.expand,
          children: [
            // Dark base mesh
            Container(color: AppTheme.bg),
            // Smoke Canvas
            CustomPaint(
              painter: _SmokePainter(particles),
            ),
            // Content
            widget.child,
          ],
        ),
      ),
    );
  }
}

class Particle {
  double x, y, vx, vy, radius, alpha;
  Particle({
    required this.x, required this.y, 
    required this.vx, required this.vy, 
    required this.radius, required this.alpha
  });
}

class _SmokePainter extends CustomPainter {
  final List<Particle> particles;
  
  _SmokePainter(this.particles);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..blendMode = BlendMode.screen
      ..imageFilter = ui.ImageFilter.blur(sigmaX: 40, sigmaY: 40);

    for (var p in particles) {
      paint.shader = ui.Gradient.radial(
        Offset(p.x, p.y),
        p.radius,
        [
          const Color(0xFFFF7800).withOpacity(p.alpha), // Vibrant Orange
          const Color(0xFFFF7800).withOpacity(0.0),
        ],
      );
      canvas.drawCircle(Offset(p.x, p.y), p.radius, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _SmokePainter oldDelegate) => true;
}
