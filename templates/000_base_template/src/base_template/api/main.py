"""
목적: FastAPI 앱을 최소 구성으로 실행하기 위한 엔트리 포인트 제공
설명: 헬스체크/Chat API와 정적 UI 제공을 포함한 실행 엔트리이다.
디자인 패턴: 단일 책임 원칙(SRP)
참조: src/base_template/static
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from base_template.shared.config import RuntimeEnvironmentLoader

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

# 런타임 환경(local/dev/stg/prod)을 판별해 환경 파일을 로드한다.
RUNTIME_ENV = RuntimeEnvironmentLoader().load()

# NOTE:
# .env 로딩 이후에 라우터/서비스를 import해야, import 시점에 생성되는 노드/모델이
# 최신 환경 변수를 정상적으로 읽을 수 있다.
from base_template.api.chat.routers import router as chat_router
from base_template.api.chat.services import shutdown_chat_api_service
from base_template.api.health.routers.server import router as health_router
from base_template.api.ui.routers import router as ui_chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 종료 시 Chat 서비스 리소스를 정리한다."""
    try:
        yield
    finally:
        shutdown_chat_api_service()


app = FastAPI(lifespan=lifespan)
app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(ui_chat_router)

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    """기본 접속 시 문서 페이지로 리다이렉트한다."""
    return RedirectResponse(url="/docs")
