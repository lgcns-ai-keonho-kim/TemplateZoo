# `fs/base/engine.py` 레퍼런스

이 문서는 `src/chatbot/integrations/fs/base/engine.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | 파일 시스템 엔진 인터페이스를 제공한다. |
| 설명 | 파일 쓰기/읽기/목록/이동/복사를 위한 표준 메서드를 정의한다. |
| 디자인 패턴 | 전략 패턴 |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `BaseFSEngine` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `fs/base/engine.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `파일 쓰기/읽기/목록/이동/복사를 위한 표준 메서드를 정의한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. 파일 시스템 엔진은 `BaseFSEngine` 계약을 구현하는 중심 모듈이므로 메서드 시그니처와 예외 의미를 구현체 간 일관되게 유지해야 한다.
2. 경로 기준(`base_dir`, `path`, `suffix`) 해석이 구현체마다 달라지면 상위 `FileLogRepository`가 깨지므로 의미를 임의로 넓히지 않는 편이 안전하다.

## 5. 추가 개발과 확장 시 주의점

1. 원격 스토리지 구현을 추가할 때도 `BaseFSEngine`의 최소 인터페이스만 구현하고, 인증/재시도는 구현체 내부에서 해결하는 편이 좋다.
2. 새 엔진을 공개 API에 노출하려면 `src/chatbot/integrations/fs/__init__.py`와 overview 문서를 함께 갱신해야 한다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/fs/base/engine.py`
- `src/chatbot/integrations/fs/engines/local.py`
