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
      
    final rng = Random(42); // Fixed seed for consistent look
    for (int i = 0; i < 25; i++) {
        double ox = rng.nextDouble() * 1600;
        double oy = rng.nextDouble() * 1200;
        particles.add(Particle(
          originX: ox,
          originY: oy,
          x: ox,
          y: oy,
          vx: (rng.nextDouble() - 0.5) * 0.4,
          vy: (rng.nextDouble() - 0.5) * 0.4,
          radius: 250 + rng.nextDouble() * 450,
          alpha: 0.04 + rng.nextDouble() * 0.06,
        ));
    }
  }

  void _updateParticles() {
    final Size size = MediaQuery.of(context).size.isEmpty 
        ? const Size(1600, 1200) 
        : MediaQuery.of(context).size;
        
    for (var p in particles) {
      p.x += p.vx;
      p.y += p.vy;

      double dx = pointer.dx - p.x;
      double dy = pointer.dy - p.y;
      double dist = sqrt(dx * dx + dy * dy);
      
      if (dist < 500.0) {
        double strength = 0.15 + (cursorSpeed * 0.02);
        p.vx += (dx / dist) * strength;
        p.vy += (dy / dist) * strength;
      } else {
        double oxd = p.originX - p.x;
        double oyd = p.originY - p.y;
        p.vx += oxd * 0.001;
        p.vy += oyd * 0.001;
      }
      
      double speed = sqrt(p.vx * p.vx + p.vy * p.vy);
      if (speed > 6.0) {
          p.vx = (p.vx / speed) * 6.0;
          p.vy = (p.vy / speed) * 6.0;
      }
      
      p.vx *= 0.97;
      p.vy *= 0.97;
      
      // Gentle random drift
      p.vx += (Random().nextDouble() - 0.5) * 0.03;
      p.vy += (Random().nextDouble() - 0.5) * 0.03;

      if (p.x < -400) p.x = size.width + 400;
      if (p.x > size.width + 400) p.x = -400;
      if (p.y < -400) p.y = size.height + 400;
      if (p.y > size.height + 400) p.y = -400;
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
            // Dark base
            Container(color: AppTheme.bg),
            // Smoke in isolated repaint boundary — won't trigger child rebuilds
            RepaintBoundary(
              child: CustomPaint(
                painter: _SmokePainter(particles),
              ),
            ),
            // Content in its own repaint boundary
            RepaintBoundary(
              child: widget.child,
            ),
          ],
        ),
      ),
    );
  }
}

class Particle {
  double originX, originY, x, y, vx, vy, radius, alpha;
  
  Particle({
    required this.originX, required this.originY,
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
    // No ImageFilter.blur — use multi-stop radial gradients for smooth falloff
    final paint = Paint()..blendMode = BlendMode.screen;

    for (var p in particles) {
      double a = min(p.alpha, 0.12);
      paint.shader = ui.Gradient.radial(
        Offset(p.x, p.y),
        p.radius,
        [
          const Color(0xFFFF7800).withOpacity(a),
          const Color(0xFFFF6000).withOpacity(a * 0.6),
          const Color(0xFFFF4500).withOpacity(a * 0.2),
          const Color(0xFFFF4500).withOpacity(0.0),
        ],
        [0.0, 0.3, 0.7, 1.0], // Smooth multi-stop falloff
      );
      canvas.drawCircle(Offset(p.x, p.y), p.radius, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _SmokePainter oldDelegate) => true;
}
