#!/usr/bin/env bash
set -euo pipefail

output_file="project_dump.txt"
debug_log="debug_skipped.log"

# Ограничения (лучше держать умеренно, иначе не влезет в чат)
max_bytes=$((1200 * 1024))        # 1.2MB на файл
max_total=$((20 * 1024 * 1024))   # 20MB всего (можно менять)

# Сам скрипт (как он запущен)
script_path="$0"
script_base="$(basename "$script_path")"

# Что включаем (маски)
include_globs=(
  "*.md" "*.txt" "*.dart" "*.yaml" "*.yml" "*.log"
  "*.json" "*.toml" "*.ini" "*.py" "*.sh"
  "*.gradle" "*.properties" "pubspec.lock"
  "pubspec.yaml" "Dockerfile" "dockerfile"
  "Makefile" "makefile" ".gitignore" ".Gitignore"
  "*.sql" "*.mako" "*.cfg" "*.conf" "*.config"
)

# Что исключаем (директории)
exclude_dirs=(
  ".git" ".dart_tool" "build" ".idea"
  ".vscode" "node_modules" "dist" "target"
  ".gradle" ".next" ".cache"
)

# Собираем выражение prune для директорий
exclude_find=()
for dir in "${exclude_dirs[@]}"; do
  exclude_find+=( -name "$dir" -prune -o )
done

# Собираем выражение include по маскам
include_find=()
for g in "${include_globs[@]}"; do
  include_find+=( -name "$g" -o )
done
unset 'include_find[${#include_find[@]}-1]' 2>/dev/null || true  # убираем последний -o

# Заголовок + структура
{
  echo "=== PROJECT DUMP ==="
  echo "Generated: $(date -Iseconds)"
  echo "Root: $(pwd)"
  echo

  echo "=== TREE (FILES ONLY) ==="
  if command -v tree >/dev/null 2>&1; then
    tree -a -I '.git|node_modules|build|dist|target|.dart_tool|.idea|.vscode|.gradle|.next|.cache' --filesfirst 2>/dev/null || true
  else
    find . -type f \( "${exclude_find[@]}" -false \) -o -print | sort 2>/dev/null || true
  fi

  echo
  echo "=== FILE CONTENTS ==="
} > "$output_file"

echo "=== DEBUG LOG ===" > "$debug_log"
echo "Started: $(date -Iseconds)" >> "$debug_log"

total=0
processed_files=0
skipped_files=0

# Список файлов (отсортирован, устойчивый порядок)
find . \
  \( "${exclude_find[@]}" -false \) -o \
  -type f \
  \( -path "./$output_file" -o -path "./$debug_log" -o -name "$script_base" \) -prune -o \
  \( "${include_find[@]}" \) -print0 \
| sort -z \
| while IFS= read -r -d '' file; do
    # Текстовый ли файл (несколько проверок)
    is_text=false
    if file --mime-type -b "$file" 2>/dev/null | grep -q -E "^(text/|application/json|application/xml)"; then
      is_text=true
    elif LC_ALL=C grep -Iq . "$file" 2>/dev/null; then
      is_text=true
    elif [[ ! -s "$file" ]]; then
      is_text=true
    fi

    if [[ "$is_text" == "false" ]]; then
      echo "[Non-text] $file" >> "$debug_log"
      skipped_files=$((skipped_files + 1))
      continue
    fi

    size=$(wc -c < "$file" 2>/dev/null | tr -d ' ' || echo "0")

    if (( size > max_bytes )); then
      echo "[Too large: ${size} bytes] $file" >> "$debug_log"
      {
        echo "========================================"
        echo "FILE: $file"
        echo "NOTE: skipped (too large: ${size} bytes > ${max_bytes})"
        echo "========================================"
        echo
      } >> "$output_file"
      skipped_files=$((skipped_files + 1))
      continue
    fi

    if (( total + size > max_total )); then
      echo "[Max total reached: ${total} + ${size} > ${max_total}] $file" >> "$debug_log"
      {
        echo "========================================"
        echo "NOTE: reached max_total=${max_total} bytes, stopping."
        echo "========================================"
        echo "Total processed: ${total} bytes in ${processed_files} files"
        echo "Total skipped: ${skipped_files} files"
      } >> "$output_file"
      break
    fi

    {
      echo "========================================"
      echo "FILE: $file"
      echo "========================================"
      echo
      if [[ -r "$file" ]]; then
        # Нормализация CRLF
        sed 's/\r$//' "$file" 2>/dev/null || echo "[Error reading file]"
      else
        echo "[File not readable]"
      fi
      echo
      echo
    } >> "$output_file"

    total=$((total + size))
    processed_files=$((processed_files + 1))

    if (( processed_files % 50 == 0 )); then
      echo "Processed ${processed_files} files, total ${total} bytes" >&2
    fi
  done

{
  echo "========================================"
  echo "SUMMARY:"
  echo "Total files processed: ${processed_files}"
  echo "Total files skipped: ${skipped_files}"
  echo "Total bytes written: ${total}"
  echo "Output file: ${output_file}"
  echo "Script excluded: ${script_base}"
  echo "========================================"
} >> "$output_file"

echo >> "$debug_log"
echo "Total processed: ${processed_files} files" >> "$debug_log"
echo "Total skipped: ${skipped_files} files" >> "$debug_log"
echo "Debug log saved to: $debug_log" >> "$debug_log"

echo "Done. Processed ${processed_files} files, skipped ${skipped_files} files."
echo "Check $debug_log for details on skipped files."
