"""
목적: FastAPI 앱을 최소 구성으로 실행하기 위한 엔트리 포인트 제공
설명: 헬스체크 엔드포인트 1개와 정적 UI 제공만 포함
디자인 패턴: 단일 책임 원칙(SRP)
참조: src/base_template/static
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from base_template.api.health.routers.server import router as health_router

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()
app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")
app.include_router(health_router)

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    """기본 접속 시 문서 페이지로 리다이렉트한다."""
    return RedirectResponse(url="/docs")
