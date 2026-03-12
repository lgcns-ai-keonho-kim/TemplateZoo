# `db/engines/postgres/vector_adapter.py` 레퍼런스

이 문서는 `src/chatbot/integrations/db/engines/postgres/vector_adapter.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | PGVector 타입 어댑터를 제공한다. |
| 설명 | pgvector 타입 등록, 파라미터 생성, 결과 파싱을 통합한다. |
| 디자인 패턴 | 어댑터 패턴 |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `PostgresVectorAdapter` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `db/engines/postgres/vector_adapter.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `pgvector 타입 등록, 파라미터 생성, 결과 파싱을 통합한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. 벡터 직렬화/역직렬화 형식은 저장된 데이터와 직접 연결되므로 기존 데이터 호환성 없이 바꾸면 안 된다.
2. 거리 계산 기준이나 차원 검증 규칙을 추가할 때는 상위 vector store와 같이 점검해야 한다.

## 5. 추가 개발과 확장 시 주의점

1. 새 연동 구현을 추가할 때는 현재 기본 런타임에서 실제로 사용하는지, 예시 수준인지 문서에서 분리해 설명해야 한다.
2. 공개 API에 노출하는 경우 `__init__.py` export와 overview 문서를 함께 갱신해야 한다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/db/engines/postgres/vector_adapter.py`
- `src/chatbot/integrations/db/engines/postgres/engine.py`
