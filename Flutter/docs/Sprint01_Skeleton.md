# LifeMerge Flutter Skeleton

This PR adds the initial Flutter codebase skeleton for Sprint 01 (foundation + A1).

## Included
- Clean-ish module layout: `core/` and `features/<feature>/{presentation,application,domain,data}`
- Riverpod DI container bootstrap
- go_router `AppRouter` with shell navigation
- `AppTheme` based on UI Kit v1.0 tokens (Colors.md, Typography.md)

## Next
- Generate full Flutter platform scaffolds (android/ios/etc.) in a dedicated PR
- Replace placeholder screens with feature implementations
