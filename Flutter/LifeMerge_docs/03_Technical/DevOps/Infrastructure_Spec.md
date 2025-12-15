# Infrastructure Spec — Draft Environment

## Контур
- **Кластер**: K8s (managed, 3×nodes t3.medium/4vCPU/8GB), отдельный namespace `draft-*` на общем кластере с Dev.
- **Сеть**: ingress с базовой аутентификацией, IP allowlist ограничен офис/VPN; egress через NAT с ограничением к внешним API.
- **БД**: отдельный PostgreSQL instance per-branch (`draft_<branch>`), размер до 10 GB, авто-удаление с retention 2 дня.
- **Файлы**: S3 совместимое хранилище с bucket `lifemerge-draft` и prefix `branches/<branch>/`; lifecycle 7 дней.
- **Кэш/очереди**: Redis c ограничением 256MB per-namespace, RabbitMQ shared vhost `draft`.

## Конфигурация сервисов
- **Backend/AI**: деплой через Helm-чарты `charts/backend` и `charts/ai` с overlays `values/draft.yaml`.
- **Мобильные билд-серверы**: билд-агенты в CI (Linux/macOS runners) с кэшем зависимостей; артефакты в `artifacts/draft/`.
- **Secrets/Config**: `values/secrets-draft.yaml` формируются из Vault; токены интеграций заменяются на моки.

## Наблюдаемость
- Логи: stdout → Loki/ELK с label `env=draft`.
- Метрики: Prometheus scrape `draft-*`; дашборд Grafana “Draft Stand” с SLA: error rate <2%, аптайм 95%.
- Трейсинг: OpenTelemetry с экспортом в Jaeger, сэмплинг 5% для контроля нагрузки.

## Политики безопасности
- RBAC: доступ к namespace только через сервис-аккаунт CI и группу DevOps-readonly.
- Образы проходят проверку Trivy, сигнатуры Notary; pull только из приватного registry через imagePullSecrets.
- NetworkPolicy закрывает межсервисное общение, разрешает только ingress от IngressController и egress к Redis/DB.

## Интеграция с CI/CD
- Pipeline создаёт namespace, секреты и параметры БД динамически, затем применяет `helm upgrade --install`.
- После завершения MR job `cleanup_draft` удаляет namespace, PVC и префикс в S3, освобождая квоты.
- Для экономии ресурсов включена автопауза pod при простое (keda/hpa до 0 реплик) и cron на удаление старых артефактов.
