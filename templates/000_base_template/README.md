# BASE TEMPLATE

## PROJECT OVERVIEW

- 이 프로젝트는 추후 서비스 구현 예제를 위한 Boilerplate입니다.
- 이 프로젝트를 복제하신 이후, 셋업 과정에서 다음의 과정을 거치세요.

```text
# 1. 프로젝트명 / 패키지명 초기화 (문자열 치환 포함)
# - 실행이 끝나면 init.sh는 자동으로 삭제됩니다.
bash init.sh my-project my_project

# 2. 개발을 위한 가상환경 설정
uv venv .venv
uv sync 

# 3. README.md를 프로젝트에 맞게 수정해주세요.
```


## PROJECT ARCHITECTURE

- Frontend: Mounted at `<FASTAPI_SERVER_URL>/chat` 
  - src/base_template/static

- Backend
  - Core Layer
    - src/base_template/core
  - API Layer
    - src/base_template/
	- src/base_template/api/main.py: API 서버를 실행시키는 코드

## FRONTEND ARCHITECTURE (`src/base_template/static/`)

- index.html 
- assets/
- css/ 
- js/

## BACKEND ARCHITECTURE 

- API 서버 기동 코드

```bash
# uv로 main.py를 실행
uv run python3 src/<project_name>/api/main.py
# 또는 uvicorn으로 실행
uv run uvicorn <project_name>.api.main:app --host 0.0.0.0 --port 8000 --reload 
```
