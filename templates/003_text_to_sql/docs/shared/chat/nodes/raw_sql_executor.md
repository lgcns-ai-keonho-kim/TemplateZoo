# nodes/raw_sql_executor.py

읽기 전용 raw SQL 실행기입니다.

## 1. 역할

- LLM이 생성한 SQL 문자열을 실제 DB에 실행합니다.
- 현재는 `postgres`, `sqlite`만 지원합니다.
- 실행 전 최소 안전 가드를 적용합니다.

## 2. 실행 규칙

1. 단일 statement만 허용합니다.
2. `SELECT` 또는 `WITH ... SELECT`만 허용합니다.
3. `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER`, `BEGIN`, `COMMIT`, `ROLLBACK`은 차단합니다.
4. 실행 결과는 `list[dict[str, object]]` 형태로 정규화합니다.

## 3. 반환 형태

| 필드 | 설명 |
| --- | --- |
| `status` | `ok` 또는 `fail` |
| `code` | 실행 결과 코드 |
| `message` | 오류 메시지 |
| `sql` | 실제 실행 SQL |
| `rows` | 결과 행 |
| `row_count` | 결과 행 수 |

## 4. 실패 처리

- PostgreSQL 실행 실패 시 rollback을 수행합니다.
- rollback도 실패하면 연결을 재설정합니다.
- SQL 형식 오류는 `RAW_SQL_INVALID_FORMAT`으로 반환합니다.
- DB 실행 오류는 `RAW_SQL_EXECUTION_FAILED`로 반환합니다.

## 5. 관련 코드

- `src/text_to_sql/core/chat/nodes/raw_sql_execute_node.py`
- `src/text_to_sql/core/chat/nodes/raw_sql_retry_prepare_node.py`
