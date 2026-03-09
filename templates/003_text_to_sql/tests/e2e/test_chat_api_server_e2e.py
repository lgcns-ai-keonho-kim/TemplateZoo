"""
목적: Chat API 서버 E2E 테스트를 제공한다.
설명: 실제 uvicorn 서버에 HTTP 요청을 보내 세션/스트림/이력 핵심 흐름을 검증한다.
      테스트 본문은 케이스 모듈로 분리하고, 본 파일은 pytest 엔트리 포인트로 유지한다.
디자인 패턴: 블랙박스 E2E 테스트
참조: tests/conftest.py, tests/e2e/_chat_api_e2e_cases.py
"""

from __future__ import annotations

import httpx

from tests.e2e._chat_api_e2e_cases import (
    run_create_and_list_sessions,
    run_delete_session_via_ui_api,
    run_raw_sql_query_succeeds,
    run_safeguard_rejection_case,
    run_stream_and_history,
)


def test_create_and_list_sessions(chat_api_client: httpx.Client) -> None:
    """세션 생성 후 목록 조회에서 동일 세션이 보이는지 확인한다."""

    run_create_and_list_sessions(chat_api_client)


def test_delete_session_via_ui_api(chat_api_client: httpx.Client) -> None:
    """UI API로 세션을 삭제하면 목록/메시지 조회에서 제거되는지 확인한다."""

    run_delete_session_via_ui_api(chat_api_client)


def test_raw_sql_query_succeeds(chat_api_client: httpx.Client) -> None:
    """raw SQL 질의가 실제 실행 성공 결과를 반환하는지 확인한다."""

    run_raw_sql_query_succeeds(chat_api_client)


def test_stream_and_history(chat_api_client: httpx.Client) -> None:
    """단일 스트림 호출 2회 후 세션 이력이 eventual consistency로 반영되는지 확인한다."""

    run_stream_and_history(chat_api_client)


def test_safeguard_rejection_case(chat_api_client: httpx.Client) -> None:
    """Safeguard 차단 입력 시 done 이후 이력이 eventual consistency로 반영되는지 확인한다."""

    run_safeguard_rejection_case(chat_api_client)
