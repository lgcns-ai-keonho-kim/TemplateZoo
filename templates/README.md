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

<b><I>2. 파이썬 프로젝트의 이름을 항상 Rename 해주세요.</I></b>

```text
Step 1. 다음 파일들에서 프로젝트명 관련된 부분을 변경해주세요.
- pyproject.toml
- src/<project_name>
```

```bash
# Step2. 다음의 명령어를 차례로 실행해주세요.
rm -rf .venv # sudo 권한으로 실행해야 할 수도 있습니다.
uv venv .venv
uv sync
```

```bash
# Step 3. 파이썬 서버가 실행되는지 확인해주세요.
# uv로 main.py를 실행합니다.
uv run python3 src/<project_name>/api/main.py
# 또는 uvicorn으로 실행 할 수 있습니다.
uv run uvicorn <project_name>.main:app --host 0.0.0.0 --port 8000 --reload
```

<b><I>3. 항상 서버가 실행되는를 확인 후 최종적으로 PR을 요청해주세요.</I></b>
