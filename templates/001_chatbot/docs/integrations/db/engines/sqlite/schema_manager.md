# `db/engines/sqlite/schema_manager.py` 레퍼런스

이 문서는 `src/chatbot/integrations/db/engines/sqlite/schema_manager.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | SQLite 스키마 관리 모듈을 제공한다. |
| 설명 | 컬렉션 생성/삭제와 컬럼 추가/삭제를 담당한다. |
| 디자인 패턴 | 매니저 패턴 |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `SqliteSchemaManager` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `db/engines/sqlite/schema_manager.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `컬렉션 생성/삭제와 컬럼 추가/삭제를 담당한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. 스키마 생성/변경 로직은 idempotent 해야 하며 이미 존재하는 컬럼/인덱스 처리 정책을 유지해야 한다.
2. 컬렉션 스키마의 기본 키, payload, vector 필드 규칙을 문서와 같이 갱신해야 저장소 초기화 오류를 줄일 수 있다.

## 5. 추가 개발과 확장 시 주의점

1. 새 연동 구현을 추가할 때는 현재 기본 런타임에서 실제로 사용하는지, 예시 수준인지 문서에서 분리해 설명해야 한다.
2. 공개 API에 노출하는 경우 `__init__.py` export와 overview 문서를 함께 갱신해야 한다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/db/engines/sqlite/schema_manager.py`
- `src/chatbot/integrations/db/engines/sqlite/engine.py`
