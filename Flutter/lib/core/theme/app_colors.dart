import 'package:flutter/material.dart';

/// UI Kit v1.0 color tokens.
/// Source of truth: Colors.md
///
/// Do not use raw Color(...) values in UI.
abstract final class AppColors {
  static const Color primary = Color(0xFF5B8DEF);
  static const Color primaryDark = Color(0xFF3562C2);

  static const Color background = Color(0xFF0F1115);
  static const Color surface = Color(0xFF181C22);

  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFFB8C2D1);

  static const Color error = Color(0xFFFF3B30);
  static const Color success = Color(0xFF34C759);
  static const Color accent = Color(0xFFFF9F1C);
}
