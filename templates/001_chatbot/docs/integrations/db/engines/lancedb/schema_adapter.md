# `db/engines/lancedb/schema_adapter.py` 레퍼런스

이 문서는 `src/chatbot/integrations/db/engines/lancedb/schema_adapter.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | LanceDB 스키마/행 변환 어댑터를 제공한다. |
| 설명 | CollectionSchema를 PyArrow 스키마로 변환하고, 입력 row를 스키마 타입으로 정규화한다. |
| 디자인 패턴 | 어댑터 패턴 |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `LanceSchemaAdapter` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `db/engines/lancedb/schema_adapter.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `CollectionSchema를 PyArrow 스키마로 변환하고, 입력 row를 스키마 타입으로 정규화한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. 외부 스키마 형식과 내부 `CollectionSchema`를 연결하는 경계이므로 필드 의미를 임의로 바꾸지 말아야 한다.
2. 차원 정보나 vector 필드명을 바꾸면 벡터 검색 결과 전체에 영향을 준다.

## 5. 추가 개발과 확장 시 주의점

1. 새 연동 구현을 추가할 때는 현재 기본 런타임에서 실제로 사용하는지, 예시 수준인지 문서에서 분리해 설명해야 한다.
2. 공개 API에 노출하는 경우 `__init__.py` export와 overview 문서를 함께 갱신해야 한다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/db/engines/lancedb/schema_adapter.py`
- `src/chatbot/integrations/db/base/models.py`
