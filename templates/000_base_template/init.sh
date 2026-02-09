#!/usr/bin/env bash
# ------------------------------------------------------------
# 목적: 프로젝트명/패키지명 초기화 및 문자열 치환 자동화
# 설명: 입력받은 프로젝트 슬러그와 패키지명을 기반으로
#       디렉토리명 변경과 텍스트 치환을 수행합니다.
# 사용된 디자인 패턴: 절차적 스크립트 패턴(단일 진입점)
# 참고: pyproject.toml, README.md, uv.lock, src/base_template
# ------------------------------------------------------------

set -euo pipefail

if [ "${1-}" = "" ] || [ "${2-}" = "" ]; then
  echo "사용법: bash init.sh <프로젝트_슬러그> <패키지명>"
  echo "예시:   bash init.sh my-project my_project"
  exit 1
fi

PROJECT_SLUG="$1"
PACKAGE_NAME="$2"
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
else
  echo "알림: src/base_template 디렉토리를 찾지 못했습니다. (이미 변경되었을 수 있습니다)"
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
    "$file"
}

for target in README.md pyproject.toml uv.lock src; do
  if [ -d "$target" ]; then
    while IFS= read -r -d '' file; do
      replace_in_file "$file"
    done < <(find "$target" -type f -print0)
  elif [ -f "$target" ]; then
    replace_in_file "$target"
  fi
done

echo "완료: 프로젝트명/패키지명 변경 및 문자열 치환을 마쳤습니다."