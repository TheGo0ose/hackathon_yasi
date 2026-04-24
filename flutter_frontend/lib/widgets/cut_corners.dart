import 'package:flutter/material.dart';

class CutCornerClipper extends CustomClipper<Path> {
  final double cutSize;
  final bool topLeft;
  final bool topRight;
  final bool bottomLeft;
  final bool bottomRight;

  CutCornerClipper({
    this.cutSize = 24.0,
    this.topLeft = false,
    this.topRight = false,
    this.bottomLeft = false,
    this.bottomRight = false,
  });

  @override
  Path getClip(Size size) {
    Path path = Path();

    // Top Left
    if (topLeft) {
      path.moveTo(0, cutSize);
      path.lineTo(cutSize, 0);
    } else {
      path.moveTo(0, 0);
    }

    // Top Right
    if (topRight) {
      path.lineTo(size.width - cutSize, 0);
      path.lineTo(size.width, cutSize);
    } else {
      path.lineTo(size.width, 0);
    }

    // Bottom Right
    if (bottomRight) {
      path.lineTo(size.width, size.height - cutSize);
      path.lineTo(size.width - cutSize, size.height);
    } else {
      path.lineTo(size.width, size.height);
    }

    // Bottom Left
    if (bottomLeft) {
      path.lineTo(cutSize, size.height);
      path.lineTo(0, size.height - cutSize);
    } else {
      path.lineTo(0, size.height);
    }

    path.close();
    return path;
  }

  @override
  bool shouldReclip(covariant CutCornerClipper oldClipper) {
    return oldClipper.cutSize != cutSize ||
        oldClipper.topLeft != topLeft ||
        oldClipper.topRight != topRight ||
        oldClipper.bottomLeft != bottomLeft ||
        oldClipper.bottomRight != bottomRight;
  }
}

class CutCornerButton extends StatelessWidget {
  final String text;
  final VoidCallback onTap;
  final Color backgroundColor;

  const CutCornerButton({
    super.key,
    required this.text,
    required this.onTap,
    this.backgroundColor = const Color(0xFFFF5A36), // peachAccent
  });

  @override
  Widget build(BuildContext context) {
    return ClipPath(
      clipper: CutCornerClipper(cutSize: 20, bottomLeft: true, topRight: true),
      child: Material(
        color: backgroundColor,
        child: InkWell(
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 20),
            child: Text(
              text.toUpperCase(),
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: Colors.white,
                    letterSpacing: 2.0,
                    fontWeight: FontWeight.w800,
                  ),
            ),
          ),
        ),
      ),
    );
  }
}
