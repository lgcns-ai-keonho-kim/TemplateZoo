# `db/engines/sqlite/condition_builder.py` 레퍼런스

이 문서는 `src/chatbot/integrations/db/engines/sqlite/condition_builder.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | SQLite 조건 빌더 모듈을 제공한다. |
| 설명 | 필터 모델을 SQLite WHERE 절로 변환하고 메모리 필터 평가를 수행한다. |
| 디자인 패턴 | 빌더 패턴 |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `SqliteConditionBuilder` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `db/engines/sqlite/condition_builder.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `필터 모델을 SQLite WHERE 절로 변환하고 메모리 필터 평가를 수행한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. SQL 조건 문자열 조합 규칙이 바뀌면 SQLite/PostgreSQL 전체 조회 경로에 영향을 주므로 파라미터 순서를 안정적으로 유지해야 한다.
2. 컬럼명 인용 규칙을 손대면 예약어 충돌이나 SQL 오류가 발생할 수 있으므로 엔진별 문법 차이를 함께 확인해야 한다.

## 5. 추가 개발과 확장 시 주의점

1. 새 연동 구현을 추가할 때는 현재 기본 런타임에서 실제로 사용하는지, 예시 수준인지 문서에서 분리해 설명해야 한다.
2. 공개 API에 노출하는 경우 `__init__.py` export와 overview 문서를 함께 갱신해야 한다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/db/engines/sqlite/condition_builder.py`
- `src/chatbot/integrations/db/base/models.py`
