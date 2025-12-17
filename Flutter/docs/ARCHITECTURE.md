# Flutter Architecture

- `lib/core` contains shared infrastructure (DI, routing, theme).
- `lib/features/<feature>/{presentation,application,domain,data}` is the default feature layout.
- Feature modules must not import each other directly. Shared code goes to `core/`.

Routing:
- `go_router` with a shell route for main navigation.

State management:
- `flutter_riverpod`.

Theme:
- `AppTheme` uses UI Kit tokens.
