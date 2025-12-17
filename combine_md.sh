#!/usr/bin/env bash
set -u -o pipefail

OUTPUT_FILE="${1:-project_context.md}"

INCLUDE_UNTRACKED=true
MAX_FILE_BYTES=$((300 * 1024 * 1024))          # 300 MB
MAX_TOTAL_BYTES=$((10 * 1024 * 1024 * 1024))   # 10 GB
SKIP_MINIFIED=true
SKIP_LOCKS=true
SKIP_EXT_REGEX='\.(png|jpg|jpeg|gif|webp|ico|pdf|zip|tar|gz|7z|rar|exe|dll|so|dylib|bin|woff2?|ttf|eot|mp4|mov|avi|mkv|mp3|wav|svg)$'

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Ошибка: текущая директория не является git-репозиторием" >&2
  exit 1
fi

lang_for() {
  case "$1" in
    *.sh) echo "bash" ;;
    *.py) echo "python" ;;
    *.js) echo "javascript" ;;
    *.ts) echo "typescript" ;;
    *.tsx) echo "tsx" ;;
    *.jsx) echo "jsx" ;;
    *.json) echo "json" ;;
    *.yml|*.yaml) echo "yaml" ;;
    *.md) echo "markdown" ;;
    *.html) echo "html" ;;
    *.css) echo "css" ;;
    *.go) echo "go" ;;
    *.rs) echo "rust" ;;
    *.java) echo "java" ;;
    *.kt) echo "kotlin" ;;
    *.c|*.h) echo "c" ;;
    *.cpp|*.hpp) echo "cpp" ;;
    *) echo "" ;;
  esac
}

# Возвращает 0 если бинарный; 1 если текст; 2 если ошибка чтения
is_binary() {
  LC_ALL=C grep -qU $'\x00' "$1" 2>/dev/null
}

# Заголовок
{
  echo "# Project context"
  echo
  echo "Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
  echo
  echo "## Files"
  echo
} > "$OUTPUT_FILE"

total_bytes=0
added=0
skipped=0
skipped_unreadable=0
skipped_binary=0
skipped_large=0
skipped_filtered=0

# Генератор списка файлов (NUL-delimited) + нормальные UTF-8 пути
gen_list() {
  git -c core.quotepath=false ls-files -z
  if [ "$INCLUDE_UNTRACKED" = true ]; then
    git -c core.quotepath=false ls-files --others --exclude-standard -z
  fi
}

gen_list | while IFS= read -r -d '' file; do
  [ -z "$file" ] && continue

  # фильтры
  if [[ "$file" =~ $SKIP_EXT_REGEX ]]; then
    skipped=$((skipped+1)); skipped_filtered=$((skipped_filtered+1))
    continue
  fi
  if [ "$SKIP_MINIFIED" = true ] && [[ "$file" =~ \.min\. ]]; then
    skipped=$((skipped+1)); skipped_filtered=$((skipped_filtered+1))
    continue
  fi
  if [ "$SKIP_LOCKS" = true ]; then
    case "$file" in
      package-lock.json|yarn.lock|pnpm-lock.yaml|poetry.lock|Pipfile.lock|composer.lock|Gemfile.lock)
        skipped=$((skipped+1)); skipped_filtered=$((skipped_filtered+1))
        continue
        ;;
    esac
  fi

  # только обычные читаемые файлы
  if [ ! -f "$file" ] || [ ! -r "$file" ]; then
    {
      echo "### \`$file\`"
      echo
      echo "_SKIPPED: unreadable or not a regular file_"
      echo
    } >> "$OUTPUT_FILE"
    skipped=$((skipped+1)); skipped_unreadable=$((skipped_unreadable+1))
    continue
  fi

  # бинарность (и ошибки чтения)
  if is_binary "$file"; then
    skipped=$((skipped+1)); skipped_binary=$((skipped_binary+1))
    continue
  else
    rc=$?
    if [ $rc -eq 2 ]; then
      {
        echo "### \`$file\`"
        echo
        echo "_SKIPPED: error while scanning file (binary check)_"
        echo
      } >> "$OUTPUT_FILE"
      skipped=$((skipped+1)); skipped_unreadable=$((skipped_unreadable+1))
      continue
    fi
  fi

  # размер/строки (если вдруг wc упадёт — не валим весь скрипт)
  size="$(wc -c < "$file" 2>/dev/null | tr -d ' ' || echo 0)"
  lines="$(wc -l < "$file" 2>/dev/null | tr -d ' ' || echo 0)"

  if (( total_bytes >= MAX_TOTAL_BYTES )); then
    {
      echo "### \`$file\`"
      echo
      echo "_SKIPPED: total size limit reached (${MAX_TOTAL_BYTES} bytes)_"
      echo
    } >> "$OUTPUT_FILE"
    skipped=$((skipped+1)); skipped_large=$((skipped_large+1))
    continue
  fi

  if (( size > MAX_FILE_BYTES )); then
    {
      echo "### \`$file\`"
      echo
      echo "_SKIPPED: file too large (${size} bytes > ${MAX_FILE_BYTES} bytes), lines: ${lines}_"
      echo
    } >> "$OUTPUT_FILE"
    skipped=$((skipped+1)); skipped_large=$((skipped_large+1))
    continue
  fi

  lang="$(lang_for "$file")"

  {
    echo "### \`$file\`"
    echo
    echo "- size: ${size} bytes"
    echo "- lines: ${lines}"
    echo
    if [ -n "$lang" ]; then
      echo "\`\`\`$lang"
    else
      echo "\`\`\`"
    fi

    # Если cat упадёт — просто отметим, но продолжим
    if ! cat "$file"; then
      echo
      echo "[[READ ERROR]]"
    fi

    echo
    echo "\`\`\`"
    echo
  } >> "$OUTPUT_FILE"

  total_bytes=$((total_bytes + size))
  added=$((added+1))
done

# Итоговая статистика (дописываем в конец файла)
{
  echo "## Summary"
  echo
  echo "- added: ${added}"
  echo "- skipped: ${skipped}"
  echo "  - filtered: ${skipped_filtered}"
  echo "  - binary: ${skipped_binary}"
  echo "  - too large / total limit: ${skipped_large}"
  echo "  - unreadable/errors: ${skipped_unreadable}"
  echo
} >> "$OUTPUT_FILE"

echo "OK: wrote $OUTPUT_FILE"
