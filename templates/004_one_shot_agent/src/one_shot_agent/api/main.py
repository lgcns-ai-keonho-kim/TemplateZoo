"""
목적: FastAPI 앱을 1회성 Agent 실행 구성으로 실행한다.
설명: 헬스체크, Agent API, 정적 UI를 포함한 최소 실행 엔트리 포인트를 제공한다.
디자인 패턴: 단일 책임 원칙(SRP)
참조: src/one_shot_agent/static
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from one_shot_agent.shared.config import RuntimeEnvironmentLoader

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

# 런타임 환경(local/dev/stg/prod)을 판별해 환경 파일을 로드한다.
RUNTIME_ENV = RuntimeEnvironmentLoader().load()

# 참고:
# .env 로딩 이후에 라우터/서비스를 import해야, import 시점에 생성되는 노드/모델이
# 최신 환경 변수를 정상적으로 읽을 수 있다.
from one_shot_agent.api.agent.routers import router as agent_router
from one_shot_agent.api.agent.services import shutdown_agent_api_service
from one_shot_agent.api.health.routers.server import (
    router as health_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 종료 시 Agent 서비스 리소스를 정리한다."""
    try:
        yield
    finally:
        shutdown_agent_api_service()


app = FastAPI(lifespan=lifespan)
app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")
app.include_router(health_router)
app.include_router(agent_router)


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    """기본 접속 시 문서 페이지로 리다이렉트한다."""
    return RedirectResponse(url="/docs")
