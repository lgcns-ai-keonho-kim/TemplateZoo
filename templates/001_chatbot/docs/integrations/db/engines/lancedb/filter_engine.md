# `db/engines/lancedb/filter_engine.py` 레퍼런스

이 문서는 `src/chatbot/integrations/db/engines/lancedb/filter_engine.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | LanceDB 필터/정렬 보조 엔진을 제공한다. |
| 설명 | FilterExpression의 where 절 변환, 메모리 필터 평가, 정렬/점수 변환을 담당한다. |
| 디자인 패턴 | 정책 객체 패턴 |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `LanceFilterEngine` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `db/engines/lancedb/filter_engine.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `FilterExpression의 where 절 변환, 메모리 필터 평가, 정렬/점수 변환을 담당한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. 벡터 검색 후 후처리 필터 순서는 검색 결과 개수와 성능에 영향을 주므로 순서를 바꿀 때는 비용을 먼저 검토해야 한다.
2. 필터 표현식 해석 범위를 넓힐 때는 `Query` 모델과 충돌하지 않도록 주의해야 한다.

## 5. 추가 개발과 확장 시 주의점

1. 새 연동 구현을 추가할 때는 현재 기본 런타임에서 실제로 사용하는지, 예시 수준인지 문서에서 분리해 설명해야 한다.
2. 공개 API에 노출하는 경우 `__init__.py` export와 overview 문서를 함께 갱신해야 한다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/db/engines/lancedb/filter_engine.py`
- `src/chatbot/integrations/db/base/models.py`
