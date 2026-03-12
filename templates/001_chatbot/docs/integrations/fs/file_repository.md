# `fs/file_repository.py` 레퍼런스

이 문서는 `src/chatbot/integrations/fs/file_repository.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | 파일 기반 로그 저장소를 제공한다. |
| 설명 | 파일 시스템 엔진을 통해 날짜-UUID.log 파일로 로그를 저장한다. |
| 디자인 패턴 | 저장소 패턴 |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `FileLogRepository` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `fs/file_repository.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `파일 시스템 엔진을 통해 날짜-UUID.log 파일로 로그를 저장한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. 로그 파일 포맷은 운영 분석 도구가 그대로 소비할 수 있으므로 JSON 구조를 쉽게 바꾸지 말아야 한다.
2. 손상 파일 fallback 규칙을 유지해야 로그 수집 실패가 전체 조회 실패로 번지지 않는다.

## 5. 추가 개발과 확장 시 주의점

1. 압축, 아카이브, 보관 정책을 추가하려면 로그 저장 포맷을 바꾸기보다 별도 후처리 계층으로 분리하는 편이 안전하다.
2. 다른 파일 엔진을 붙일 때도 `FileLogRepository`는 `LogRepository` 계약만 유지하면 상위 계층 수정 없이 재사용할 수 있다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/fs/file_repository.py`
- `src/chatbot/integrations/fs/base/engine.py`
- `src/chatbot/integrations/fs/engines/local.py`
