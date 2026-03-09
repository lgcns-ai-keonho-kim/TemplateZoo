"""
목적: SQL 결과 수집 노드를 검증한다.
설명: alias별 실행 보고서를 성공/실패 컨텍스트와 사용자 노출용 메타로 정규화하는지 확인한다.
디자인 패턴: 노드 단위 테스트
참조: src/text_to_sql/core/chat/nodes/sql_result_collect_node.py
"""

from __future__ import annotations

from text_to_sql.core.chat.nodes.sql_result_collect_node import (
    _run_sql_result_collect_step,
)


def test_sql_result_collect_builds_success_context() -> None:
    """모든 alias가 성공하면 성공 alias와 SQL 결과 요약을 구성해야 한다."""

    result = _run_sql_result_collect_step(
        {
            "schema_snapshot": {
                "ecommerce.AGENTS": {
                    "target_alias": "ecommerce",
                    "columns": ["AGENT_NAME", "WORKING_AREA"],
                    "column_descriptions": {
                        "AGENT_NAME": "영업사원 이름",
                        "WORKING_AREA": "근무 지역",
                    },
                }
            },
            "execution_reports": {
                "ecommerce": {
                    "status": "ok",
                    "code": "RAW_SQL_OK",
                    "message": "",
                    "sql": 'SELECT "AGENT_NAME", "WORKING_AREA" FROM "data"."AGENTS"',
                    "row_count": 2,
                    "rows": [{"AGENT_NAME": "A"}, {"AGENT_NAME": "B"}],
                }
            }
        }
    )

    assert result["success_aliases"] == ["ecommerce"]
    assert result["failed_aliases"] == []
    assert result["sql_result"]["row_count_by_alias"]["ecommerce"] == 2
    answer_source_meta = result["answer_source_meta"]
    assert "ecommerce.AGENTS.AGENT_NAME" in answer_source_meta["column_ids"]
    assert answer_source_meta["column_descriptions"]["AGENT_NAME"] == "영업사원 이름"


def test_sql_result_collect_builds_failure_details() -> None:
    """실패 alias가 있으면 실패 상세와 오류 코드를 노출해야 한다."""

    result = _run_sql_result_collect_step(
        {
            "execution_reports": {
                "ecommerce": {
                    "status": "fail",
                    "code": "RAW_SQL_EXECUTION_FAILED",
                    "message": "relation does not exist",
                    "sql": "SELECT * FROM missing",
                    "row_count": 0,
                    "rows": [],
                }
            }
        }
    )

    assert result["failed_aliases"] == ["ecommerce"]
    assert result["failure_codes"] == ["RAW_SQL_EXECUTION_FAILED"]
    assert result["failure_details"][0]["message"] == "relation does not exist"
