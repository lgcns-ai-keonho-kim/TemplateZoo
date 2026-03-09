#!/usr/bin/env bash
# ------------------------------------------------------------
# 목적: 프로젝트명/패키지명 초기화 및 문자열 치환 자동화
# 설명: 전달한 프로젝트명(또는 현재 디렉토리명 추론)을 기반으로
#       프로젝트 슬러그/패키지명을 자동 생성하고
#       디렉토리명 변경과 텍스트 치환을 수행합니다.
# ------------------------------------------------------------

set -euo pipefail

usage() {
  echo "사용법: bash init.sh [프로젝트명]"
  echo "설명:   프로젝트명을 생략하면 현재 디렉토리명으로 자동 추론합니다."
  echo "예시:   bash init.sh my-project"
  echo "예시:   bash init.sh my_project"
  echo "예시:   bash init.sh"
}

infer_project_name_from_cwd() {
  local dir_name
  dir_name="$(basename "$PWD")"

  # 템플릿 폴더명(예: 001_project, 001-project) 접두 숫자는 제거한다.
  if [[ "$dir_name" =~ ^[0-9]+[_-]([a-z][a-z0-9_-]*)$ ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi

  echo "$dir_name"
}

detect_current_package_name() {
  local -a package_dirs=()
  local dir
  local uv_module_name
  uv_module_name=""

  if [ -f "pyproject.toml" ]; then
    uv_module_name="$(awk -F'"' '/^module-name[[:space:]]*=[[:space:]]*"/ {print $2; exit}' pyproject.toml || true)"
    if [[ "$uv_module_name" =~ ^[a-z][a-z0-9_]*$ ]]; then
      echo "$uv_module_name"
      return 0
    fi
  fi

  while IFS= read -r -d '' dir; do
    package_dirs+=("$(basename "$dir")")
  done < <(find src -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null || true)

  if [ "${#package_dirs[@]}" -eq 1 ]; then
    echo "${package_dirs[0]}"
    return 0
  fi

  return 1
}

detect_current_project_slug() {
  local pyproject_name
  pyproject_name=""

  if [ -f "pyproject.toml" ]; then
    pyproject_name="$(awk -F'"' '/^name[[:space:]]*=[[:space:]]*"/ {print $2; exit}' pyproject.toml || true)"
    if [[ "$pyproject_name" =~ ^[a-z][a-z0-9-]*$ ]]; then
      echo "$pyproject_name"
      return 0
    fi
  fi

  if [ -n "${CURRENT_PACKAGE_NAME-}" ]; then
    echo "${CURRENT_PACKAGE_NAME//_/-}"
    return 0
  fi

  return 1
}

if [ "${2-}" != "" ]; then
  usage
  exit 1
fi

if [ "${1-}" = "" ]; then
  PROJECT_NAME="$(infer_project_name_from_cwd)"
  echo "알림: 프로젝트명을 인자로 받지 않아 현재 디렉토리명으로 추론합니다. -> ${PROJECT_NAME}"
else
  PROJECT_NAME="$1"
fi

if ! [[ "$PROJECT_NAME" =~ ^[a-z][a-z0-9_-]*$ ]]; then
  echo "프로젝트명 형식이 올바르지 않습니다. 예: my-project 또는 my_project"
  usage
  exit 1
fi

PROJECT_SLUG="${PROJECT_NAME//_/-}"
PACKAGE_NAME="${PROJECT_NAME//-/_}"
export PROJECT_SLUG
export PACKAGE_NAME

CURRENT_PACKAGE_NAME=""
if CURRENT_PACKAGE_NAME="$(detect_current_package_name)"; then
  :
fi
CURRENT_PROJECT_SLUG=""
if CURRENT_PROJECT_SLUG="$(detect_current_project_slug)"; then
  :
fi

if ! [[ "$PROJECT_SLUG" =~ ^[a-z][a-z0-9-]*$ ]]; then
  echo "프로젝트 슬러그 형식이 올바르지 않습니다. 예: my-project"
  exit 1
fi

if ! [[ "$PACKAGE_NAME" =~ ^[a-z][a-z0-9_]*$ ]]; then
  echo "패키지명 형식이 올바르지 않습니다. 예: my_project"
  exit 1
fi

if [ -n "${CURRENT_PACKAGE_NAME}" ] && [ -d "src/${CURRENT_PACKAGE_NAME}" ] && [ "${CURRENT_PACKAGE_NAME}" != "${PACKAGE_NAME}" ]; then
  mv "src/${CURRENT_PACKAGE_NAME}" "src/${PACKAGE_NAME}"
elif [ -d "src/${PACKAGE_NAME}" ]; then
  echo "알림: src/${PACKAGE_NAME} 디렉토리는 이미 존재합니다. 디렉토리명 변경을 건너뜁니다."
else
  echo "알림: 변경할 src 패키지 디렉토리를 찾지 못했습니다. (이미 변경되었을 수 있습니다)"
fi

if sed --version >/dev/null 2>&1; then
  SED_INPLACE=(sed -i)
else
  SED_INPLACE=(sed -i "")
fi

replace_in_file() {
  local file="$1"
  local -a sed_expr=()

  if [ -n "${CURRENT_PACKAGE_NAME}" ] && [ "${CURRENT_PACKAGE_NAME}" != "${PACKAGE_NAME}" ]; then
    sed_expr+=(-e "s/${CURRENT_PACKAGE_NAME}/${PACKAGE_NAME}/g")
  fi

  # 기존 slug와 package 문자열이 같은 경우(예: chatbot) 전역 slug 치환을 하면
  # package 치환과 충돌해 이중 치환이 발생할 수 있으므로 건너뛴다.
  if [ -n "${CURRENT_PROJECT_SLUG}" ] && [ "${CURRENT_PROJECT_SLUG}" != "${PROJECT_SLUG}" ] && [ "${CURRENT_PROJECT_SLUG}" != "${CURRENT_PACKAGE_NAME}" ]; then
    sed_expr+=(-e "s/${CURRENT_PROJECT_SLUG}/${PROJECT_SLUG}/g")
  fi

  if [ "${#sed_expr[@]}" -eq 0 ]; then
    return 0
  fi

  if command -v grep >/dev/null 2>&1; then
    if ! grep -Iq . "$file"; then
      return 0
    fi
  fi
  "${SED_INPLACE[@]}" "${sed_expr[@]}" "$file"
}

normalize_pyproject() {
  if [ ! -f "pyproject.toml" ]; then
    return 0
  fi

  "${SED_INPLACE[@]}" \
    -e "s|^name[[:space:]]*=[[:space:]]*\"[^\"]*\"|name = \"${PROJECT_SLUG}\"|" \
    -e "s|^module-name[[:space:]]*=[[:space:]]*\"[^\"]*\"|module-name = \"${PACKAGE_NAME}\"|" \
    pyproject.toml
}

normalize_readme() {
  if [ ! -f "README.md" ]; then
    return 0
  fi

  "${SED_INPLACE[@]}" \
    -e "s|uv run python3 src/[a-z0-9_][a-z0-9_]*/api/main.py|uv run python3 src/${PACKAGE_NAME}/api/main.py|g" \
    -e "s|uv run uvicorn [a-z0-9_-][a-z0-9_-]*\\.api\\.main:app|uv run uvicorn ${PACKAGE_NAME}.api.main:app|g" \
    -e "s|src/[a-z0-9_][a-z0-9_]*/|src/${PACKAGE_NAME}/|g" \
    README.md
}

normalize_uv_lock() {
  if [ ! -f "uv.lock" ]; then
    return 0
  fi

  awk -v slug="${PROJECT_SLUG}" '
    function flush_block(    i) {
      if (block_n == 0) {
        return
      }
      if (editable && name_idx > 0) {
        block[name_idx] = "name = \"" slug "\""
      }
      for (i = 1; i <= block_n; i++) {
        print block[i]
      }
      delete block
      block_n = 0
      name_idx = 0
      editable = 0
    }

    /^\[\[package\]\]$/ {
      flush_block()
      block[++block_n] = $0
      next
    }

    {
      if (block_n == 0) {
        print $0
        next
      }
      block[++block_n] = $0
      if (name_idx == 0 && $0 ~ /^name = "/) {
        name_idx = block_n
      }
      if ($0 ~ /^source = \{ editable = "\." \}$/) {
        editable = 1
      }
    }

    END {
      flush_block()
    }
  ' uv.lock > uv.lock.tmp

  mv uv.lock.tmp uv.lock
}

for target in README.md pyproject.toml uv.lock src tests docs; do
  if [ -d "$target" ]; then
    while IFS= read -r -d '' file; do
      replace_in_file "$file"
    done < <(find "$target" -type f -print0)
  elif [ -f "$target" ]; then
    replace_in_file "$target"
  fi
done

normalize_pyproject
normalize_readme
normalize_uv_lock

echo "완료: 프로젝트명/패키지명 변경 및 문자열 치환을 마쳤습니다."
echo "PROJECT_SLUG=${PROJECT_SLUG}"
echo "PACKAGE_NAME=${PACKAGE_NAME}"
echo "CURRENT_PROJECT_SLUG=${CURRENT_PROJECT_SLUG:-unknown}"
echo "CURRENT_PACKAGE_NAME=${CURRENT_PACKAGE_NAME:-unknown}"
