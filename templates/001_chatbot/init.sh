#!/usr/bin/env bash
# ------------------------------------------------------------
# 목적: 프로젝트명/패키지명 초기화 및 문자열 치환 자동화
# 설명: 입력받은 단일 프로젝트명을 기반으로
#       프로젝트 슬러그/패키지명을 자동 생성하고
#       디렉토리명 변경과 텍스트 치환을 수행합니다.
# ------------------------------------------------------------

set -euo pipefail

if [ "${1-}" = "" ] || [ "${2-}" != "" ]; then
  echo "사용법: bash init.sh <프로젝트명>"
  echo "예시:   bash init.sh my-project"
  echo "예시:   bash init.sh my_project"
  exit 1
fi

PROJECT_NAME="$1"

if ! [[ "$PROJECT_NAME" =~ ^[a-z][a-z0-9_-]*$ ]]; then
  echo "프로젝트명 형식이 올바르지 않습니다. 예: my-project 또는 my_project"
  exit 1
fi

PROJECT_SLUG="${PROJECT_NAME//_/-}"
PACKAGE_NAME="${PROJECT_NAME//-/_}"
export PROJECT_SLUG
export PACKAGE_NAME

if ! [[ "$PROJECT_SLUG" =~ ^[a-z][a-z0-9-]*$ ]]; then
  echo "프로젝트 슬러그 형식이 올바르지 않습니다. 예: my-project"
  exit 1
fi

if ! [[ "$PACKAGE_NAME" =~ ^[a-z][a-z0-9_]*$ ]]; then
  echo "패키지명 형식이 올바르지 않습니다. 예: my_project"
  exit 1
fi

if [ -d "src/base_template" ]; then
  mv "src/base_template" "src/${PACKAGE_NAME}"
elif [ -d "src/chatbot" ]; then
  mv "src/chatbot" "src/${PACKAGE_NAME}"
else
  echo "알림: src/base_template 또는 src/chatbot 디렉토리를 찾지 못했습니다. (이미 변경되었을 수 있습니다)"
fi

if sed --version >/dev/null 2>&1; then
  SED_INPLACE=(sed -i)
else
  SED_INPLACE=(sed -i "")
fi

replace_in_file() {
  local file="$1"
  if command -v grep >/dev/null 2>&1; then
    if ! grep -Iq . "$file"; then
      return 0
    fi
  fi
  "${SED_INPLACE[@]}" \
    -e "s/base-template/${PROJECT_SLUG}/g" \
    -e "s/base_template/${PACKAGE_NAME}/g" \
    -e "s/chatbot/${PACKAGE_NAME}/g" \
    "$file"
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

echo "완료: 프로젝트명/패키지명 변경 및 문자열 치환을 마쳤습니다."
echo "PROJECT_SLUG=${PROJECT_SLUG}"
echo "PACKAGE_NAME=${PACKAGE_NAME}"
