# Shared 모듈 가이드

이 문서는 `src/rag_chatbot/shared`가 core와 integrations를 실제 서비스로 연결하는 방식을 설명한다.

## 1. 현재 역할

- `shared/chat`: 그래프 실행, 세션 저장, 메모리, 서비스 오케스트레이션
- `shared/runtime`: 큐, 이벤트 버퍼, 워커, 스레드풀
- `shared/config`: `.env`와 JSON/환경 변수 병합
- `shared/logging`: 로거, 저장소, 로그 모델
- `shared/exceptions`: 공통 예외 코드와 detail 모델
- `shared/const`: 전역 상수

## 2. 현재 의존 흐름

- `api -> shared -> core`
- `shared -> integrations`

## 3. 유지보수/추가개발 포인트

- 실행 흐름 변경은 `shared/chat/services`와 `shared/runtime`을 같이 봐야 한다.
- 설정 키를 추가하면 `shared/config`, `.env.sample`, `docs/setup/env.md`를 함께 맞춰야 한다.
- 공통 예외 코드를 늘릴 때는 API 매핑과 프런트 오류 노출까지 영향 범위를 확인하는 편이 좋다.

## 4. 관련 문서

- `docs/shared/chat/README.md`
- `docs/shared/runtime.md`
- `docs/shared/config.md`
- `docs/shared/logging.md`
- `docs/shared/exceptions.md`
