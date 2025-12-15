import 'package:flutter/material.dart';

import 'app_colors.dart';
import 'app_typography.dart';

abstract final class AppTheme {
  static ThemeData get light {
    final colorScheme = ColorScheme.light(
      primary: AppColors.primary,
      onPrimary: Colors.white,
      surface: Colors.white,
      onSurface: const Color(0xFF0F1115),
      error: AppColors.error,
      onError: Colors.white,
    );

    return ThemeData(
      useMaterial3: true,
      fontFamily: AppTypography.fontFamily,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: Colors.white,
      textTheme: _textTheme(isDark: false),
    );
  }

  static ThemeData get dark {
    final colorScheme = ColorScheme.dark(
      primary: AppColors.primary,
      onPrimary: Colors.white,
      surface: AppColors.surface,
      onSurface: AppColors.textPrimary,
      error: AppColors.error,
      onError: Colors.white,
    );

    return ThemeData(
      useMaterial3: true,
      fontFamily: AppTypography.fontFamily,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.background,
      textTheme: _textTheme(isDark: true),
    );
  }

  static TextTheme _textTheme({required bool isDark}) {
    final primary = isDark ? AppColors.textPrimary : const Color(0xFF0F1115);
    final secondary = isDark ? AppColors.textSecondary : const Color(0xFF3C4657);

    return TextTheme(
      headlineLarge: AppTypography.h1.copyWith(color: primary),
      headlineMedium: AppTypography.h2.copyWith(color: primary),
      titleLarge: AppTypography.h3.copyWith(color: primary),
      bodyLarge: AppTypography.body.copyWith(color: primary),
      bodyMedium: AppTypography.bodyMedium.copyWith(color: primary),
      bodySmall: AppTypography.caption.copyWith(color: secondary),
    );
  }
}
