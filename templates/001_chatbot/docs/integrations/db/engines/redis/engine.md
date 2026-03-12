# `db/engines/redis/engine.py` 레퍼런스

이 문서는 `src/chatbot/integrations/db/engines/redis/engine.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | Redis 기반 DB 엔진을 제공한다. |
| 설명 | 스키마 기반 필드 저장과 간단한 검색을 지원한다. |
| 디자인 패턴 | 어댑터 패턴 |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `RedisEngine` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `db/engines/redis/engine.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `스키마 기반 필드 저장과 간단한 검색을 지원한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. Redis 엔진은 `BaseDBEngine` 계약을 구현하는 중심 모듈이므로 반환 타입과 예외 정책을 다른 엔진과 같은 의미로 유지해야 한다.
2. 쿼리/업서트/삭제 메서드의 인자 해석이 `CollectionSchema`, `Query` 모델과 어긋나면 상위 저장소가 바로 깨지므로 계약 변경을 피해야 한다.

## 5. 추가 개발과 확장 시 주의점

1. 새 연동 구현을 추가할 때는 현재 기본 런타임에서 실제로 사용하는지, 예시 수준인지 문서에서 분리해 설명해야 한다.
2. 공개 API에 노출하는 경우 `__init__.py` export와 overview 문서를 함께 갱신해야 한다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/db/engines/redis/engine.py`
- `src/chatbot/integrations/db/base/engine.py`
