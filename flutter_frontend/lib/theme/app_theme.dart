import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static const Color bg = Color(0xFF08070C);
  static const Color bg2 = Color(0xFF0D0B13);
  static const Color surface = Color(0x08FFFFFF);
  
  static const Color peach = Color(0xFFE8A98A);
  static const Color peachLight = Color(0xFFF2C9B0);
  static const Color peachDark = Color(0xFFC4784F);
  static const Color peachAccent = Color(0xFFFF5A36); // Vibrant brand color
  
  static const Color cream = Color(0xFFF5EDE4);
  static const Color textMuted = Color(0x6BF5EDE4); // ~42%
  static const Color textDim = Color(0x38F5EDE4); // ~22%

  static const Color border = Color(0x14F5EDE4);

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: Colors.transparent,
      primaryColor: peachAccent,
      textTheme: TextTheme(
        // Massive Titles (Next-Gen style)
        displayLarge: GoogleFonts.cormorantGaramond(
          color: cream,
          fontSize: 88,
          fontWeight: FontWeight.w700,
          height: 1.0,
          letterSpacing: -0.02,
        ),
        displayMedium: GoogleFonts.inter(
          color: cream,
          fontSize: 64,
          fontWeight: FontWeight.w800,
          height: 1.05,
          letterSpacing: -0.03,
        ),
        titleLarge: GoogleFonts.inter(
          color: cream,
          fontSize: 32,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: GoogleFonts.inter(
          color: textMuted,
          fontSize: 16,
          fontWeight: FontWeight.w400,
          height: 1.6,
        ),
        labelLarge: GoogleFonts.inter(
          color: cream,
          fontSize: 14,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.1,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.transparent,
        border: const UnderlineInputBorder(
          borderSide: BorderSide(color: border),
        ),
        enabledBorder: const UnderlineInputBorder(
          borderSide: BorderSide(color: border),
        ),
        focusedBorder: const UnderlineInputBorder(
          borderSide: BorderSide(color: peachLight),
        ),
        labelStyle: GoogleFonts.inter(
          color: textDim,
          fontSize: 12,
          fontWeight: FontWeight.w500,
          letterSpacing: 1.5,
        ),
        hintStyle: GoogleFonts.inter(
          color: textDim,
          fontSize: 16,
          fontStyle: FontStyle.italic,
        ),
      ),
    );
  }
}
