import 'package:flutter/material.dart';

/// Minimal localization layer for the auth flow.
class AppLocalizations {
  AppLocalizations(this.locale);

  final Locale locale;

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('ru'),
  ];

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  String get languageCode => locale.languageCode;

  bool get isRu => languageCode == 'ru';

  String get appName => isRu ? 'LifeMerge' : 'LifeMerge';
  String get loginTitle => isRu ? 'Вход' : 'Sign in';
  String get loginSubtitle =>
      isRu ? 'Продолжайте с того места, где остановились' : 'Pick up where you left off';
  String get emailLabel => isRu ? 'Электронная почта' : 'Email';
  String get passwordLabel => isRu ? 'Пароль' : 'Password';
  String get continueButton => isRu ? 'Продолжить' : 'Continue';
  String get noAccountYet =>
      isRu ? 'Нет аккаунта?' : "Don't have an account yet?";
  String get createAccount => isRu ? 'Создать' : 'Create one';
  String get haveAccount => isRu ? 'Уже с нами?' : 'Already with us?';
  String get signIn => isRu ? 'Войти' : 'Sign in';
  String get nameLabel => isRu ? 'Имя' : 'Name';
  String get confirmPasswordLabel => isRu ? 'Повторите пароль' : 'Confirm password';
  String get registerTitle => isRu ? 'Регистрация' : 'Sign up';
  String get registerSubtitle =>
      isRu ? 'Создайте аккаунт, чтобы начать' : 'Create an account to start';
  String get passwordsDoNotMatch =>
      isRu ? 'Пароли не совпадают' : 'Passwords do not match';
  String get fieldRequired => isRu ? 'Обязательное поле' : 'Required field';
  String get invalidEmail => isRu ? 'Неверный email' : 'Invalid email';
  String get passwordTooShort =>
      isRu ? 'Минимум 8 символов' : 'Minimum 8 characters';
  String get forgotPassword => isRu ? 'Забыли пароль?' : 'Forgot password?';
  String get resetPassword => isRu ? 'Восстановить доступ' : 'Reset access';
  String get resetPasswordSent =>
      isRu ? 'Письмо для восстановления отправлено' : 'Recovery email sent';
  String get incorrectCredentials =>
      isRu ? 'Неправильный логин или пароль' : 'Incorrect email or password';
  String get accountExists =>
      isRu ? 'Аккаунт с этим email уже существует' : 'Account already exists for this email';
  String get userNotFound =>
      isRu ? 'Пользователь не найден' : 'User not found';
  String get errorTitle => isRu ? 'Ошибка' : 'Error';
  String get genericError =>
      isRu ? 'Что-то пошло не так. Попробуйте позже.' : 'Something went wrong. Try again later.';
  String get continueToApp =>
      isRu ? 'Перейти к приложению' : 'Go to the app';
  String get loading => isRu ? 'Загрузка…' : 'Loading…';
  String get signUpSuccess =>
      isRu ? 'Аккаунт создан! Проверьте почту.' : 'Account created! Check your inbox.';
  String get logout => isRu ? 'Выйти' : 'Log out';
  String get logoutDescription =>
      isRu ? 'Очистить сессию и вернуться на экран входа' : 'Clear your session and return to sign in';
  String get aiRulesTitle =>
      isRu ? 'Правила ассистента' : 'AI rules';
  String get addBreak => isRu ? 'Пауза' : 'Add break';
  String get profileScheduleTitle =>
      isRu ? 'Профиль и рабочий график' : 'Profile & work schedule';
  String get profileScheduleHint => isRu
      ? 'AI использует рабочие часы и дни, чтобы предлагать встречи и фильтровать уведомления'
      : 'AI uses your working hours and days to propose meetings and filter notifications';
  String get timezoneLabel => isRu ? 'Часовой пояс:' : 'Timezone:';
  String get quietHoursTitle => isRu ? 'Часы тишины' : 'Quiet hours';
  String get quietHoursDescription => isRu
      ? 'В это время AI не будет создавать встречи и включит режим «Не беспокоить»'
      : 'During these hours AI will avoid scheduling and enable do-not-disturb.';
  String get startLabel => isRu ? 'Начало' : 'Start';
  String get endLabel => isRu ? 'Конец' : 'End';
  String get breaksTitle => isRu ? 'Паузы и перерывы' : 'Breaks & downtime';
  String get breaksDescription => isRu
      ? 'Запланированные паузы учитываются при планировании задач и встреч'
      : 'Scheduled downtime is respected when placing tasks and meetings.';
  String durationLabel(Duration duration) => isRu
      ? 'Длительность: ${duration.inMinutes} мин.'
      : 'Duration: ${duration.inMinutes} min';
  String get forbiddenDaysTitle => isRu ? 'Запретные дни' : 'Forbidden days';
  String get forbiddenDaysDescription => isRu
      ? 'В выбранные дни AI не создаёт встречи и не беспокоит вас'
      : 'On these days AI will not schedule meetings or disturb you.';
  String get forbiddenWorkdayTooltip => isRu
      ? 'Этот день отмечен рабочим в профиле'
      : 'This is marked as a working day in your profile';
  String get forbiddenDayTooltip =>
      isRu ? 'Неназначаемый день' : 'Marked as unavailable';
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) =>
      AppLocalizations.supportedLocales.any(
        (supported) => supported.languageCode == locale.languageCode,
      );

  @override
  Future<AppLocalizations> load(Locale locale) async {
    return AppLocalizations(locale);
  }

  @override
  bool shouldReload(covariant LocalizationsDelegate<AppLocalizations> old) =>
      false;
}
