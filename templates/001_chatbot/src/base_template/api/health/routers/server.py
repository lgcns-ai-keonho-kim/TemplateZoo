"""
목적: 헬스체크 라우터 제공
설명: 서비스 상태 확인용 엔드포인트를 정의한다
디자인 패턴: 라우터 패턴
참조: src/base_template/api/main.py
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health", summary="서버의 상태를 조회합니다.")
def health_check():
    """서버의 상태를 확인합니다."""
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)
