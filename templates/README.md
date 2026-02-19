# Serivce Templates

- Contributors
  - 김건호 선임 <I>@ AI Tech Hub / Soultion Delivery</I>
  - 장선웅 선임 <I>@ AI Tech Hub / Soultion Delivery</I>

---

## Contribution Guide

<b><I> 1. 신규 예제를 작성 할 때는 항상 <a href="./001_chatbot/">chatbot</a>을 먼저 복사하세요.</I></b>

```bash
# Base Template은 모든 구현에 사용되는 기본 구조입니다.
# 최대한 구조를 지켜 작성하시되, 작성이 완료된 다음 불필요한 부분에 대해서 삭제해주세요.
cp -r 001_chatbot <TEMPLATE_NUMBER>_<STH_TITLE>
```

<b><I>2. 파이썬 프로젝트 이름은 init.sh로 반드시 초기화하세요.</I></b>

```bash
# Step 1. 복사한 템플릿 디렉토리로 이동합니다.
cd <TEMPLATE_NUMBER>_<STH_TITLE>

# Step 2-A. 프로젝트명을 자동 인식해서 초기화합니다. (권장)
# - 현재 폴더명이 002_rag_chatbot 이면 rag_chatbot 으로 인식합니다.
bash init.sh

# Step 2-B. 또는 프로젝트명을 명시해서 초기화할 수 있습니다.
bash init.sh <project_name>
```

```text
init.sh가 자동으로 반영하는 항목
- pyproject.toml: project.name, module-name
- src/<current_package> -> src/<new_package> 디렉토리명 변경
- README.md / docs / tests / src 등의 관련 문자열 치환
- README.md/uv.lock 네이밍 정책 강제 정규화
  (README import/path는 underscore 패키지명, uv.lock 루트 패키지명은 hyphen 슬러그)
```

```bash
# Step 3. 가상환경/의존성을 다시 맞춥니다.
rm -rf .venv # sudo 권한으로 실행해야 할 수도 있습니다.
uv venv .venv
uv sync
```

```bash
# Step 4. 파이썬 서버가 실행되는지 확인해주세요.
# uv로 main.py를 실행합니다.
uv run python3 src/<project_package>/api/main.py
# 또는 uvicorn으로 실행할 수 있습니다.
uv run uvicorn <project_package>.api.main:app --host 0.0.0.0 --port 8000 --reload
```

```text
예시)
1) 001_chatbot -> cp -> 002_rag_chatbot -> bash init.sh
2) 002_rag_chatbot -> cp -> 003_nl2sql_chatbot -> bash init.sh
위 흐름으로 연속 복사해도 이름이 중복 치환되지 않도록 처리되어 있습니다.
```

<b><I>3. 항상 서버가 실행되는를 확인 후 최종적으로 PR을 요청해주세요.</I></b>
