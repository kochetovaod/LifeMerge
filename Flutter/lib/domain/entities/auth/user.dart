import 'package:meta/meta.dart';

@immutable
class User {
  const User({
    required this.id,
    required this.email,
    required this.fullName,
    required this.timezone,
  });

  final String id;
  final String email;
  final String fullName;
  final String timezone;

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String? ?? '',
      email: json['email'] as String? ?? '',
      fullName: json['full_name'] as String? ?? '',
      timezone: json['timezone'] as String? ?? 'UTC',
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'email': email,
      'full_name': fullName,
      'timezone': timezone,
    };
  }
}
