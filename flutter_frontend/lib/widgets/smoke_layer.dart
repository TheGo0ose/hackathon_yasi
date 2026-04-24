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
  Offset lastPointer = const Offset(500, 500);
  double cursorSpeed = 0;

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
    for (int i = 0; i < 150; i++) {
        double ox = Random().nextDouble() * 1000;
        double oy = Random().nextDouble() * 1000;
        particles.add(Particle(
          originX: ox,
          originY: oy,
          x: ox,
          y: oy,
          vx: (Random().nextDouble() - 0.5) * 1.5,
          vy: (Random().nextDouble() - 0.5) * 1.5,
          radius: 20 + Random().nextDouble() * 160,
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
        double strength = 0.3 + (cursorSpeed * 0.05);
        p.vx += (dx / dist) * strength;
        p.vy += (dy / dist) * strength;
      } else {
        // Disperse back to uniform mesh
        double oxd = p.originX - p.x;
        double oyd = p.originY - p.y;
        p.vx += oxd * 0.002;
        p.vy += oyd * 0.002;
        // Keep moving randomly so it doesn't freeze
        p.vx += (Random().nextDouble() - 0.5) * 0.15;
        p.vy += (Random().nextDouble() - 0.5) * 0.15;
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
        lastPointer = pointer;
        pointer = e.position;
        cursorSpeed = min(sqrt(pow(pointer.dx - lastPointer.dx, 2) + pow(pointer.dy - lastPointer.dy, 2)), 100);
      },
      child: GestureDetector(
        onPanUpdate: (e) {
          lastPointer = pointer;
          pointer = e.globalPosition;
          cursorSpeed = min(sqrt(pow(pointer.dx - lastPointer.dx, 2) + pow(pointer.dy - lastPointer.dy, 2)), 100);
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
  double originX, originY, x, y, vx, vy, radius, alpha;
  double dynamicRadius = 0;
  double dynamicAlpha = 0;
  
  Particle({
    required this.originX, required this.originY,
    required this.x, required this.y, 
    required this.vx, required this.vy, 
    required this.radius, required this.alpha
  }) {
    dynamicRadius = radius;
    dynamicAlpha = alpha;
  }
}

class _SmokePainter extends CustomPainter {
  final List<Particle> particles;
  
  _SmokePainter(this.particles);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..blendMode = BlendMode.screen
      ..imageFilter = ui.ImageFilter.blur(sigmaX: 80, sigmaY: 80);

    for (var p in particles) {
      double finalAlpha = min(p.dynamicAlpha, 0.8);
      paint.shader = ui.Gradient.radial(
        Offset(p.x, p.y),
        p.dynamicRadius,
        [
          const Color(0xFFFF7800).withOpacity(finalAlpha), // Vibrant Orange
          const Color(0xFFFF7800).withOpacity(0.0),
        ],
      );
      canvas.drawCircle(Offset(p.x, p.y), p.dynamicRadius, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _SmokePainter oldDelegate) => true;
}
