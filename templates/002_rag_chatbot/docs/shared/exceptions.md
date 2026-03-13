# Shared Exceptions 가이드

이 문서는 `BaseAppException`, `ExceptionDetail`을 중심으로 한 공통 예외 모델을 설명한다.

## 1. 현재 구조

- `ExceptionDetail`: `code`, `cause`, `hint`, `metadata`를 담는 상세 모델
- `BaseAppException`: 사용자 메시지와 detail, 원본 예외를 함께 보관하는 베이스 예외

## 2. 현재 사용 방식

- core, shared, integrations는 세부 예외를 바로 노출하지 않고 `BaseAppException`으로 감싸는 편이 기본이다.
- API 계층은 `detail.code`를 기준으로 HTTP 상태 코드로 바꾼다.
- 프런트는 서버가 내려준 오류 코드와 메시지를 그대로 표시하거나 fallback 문자열을 사용한다.

## 3. 유지보수/추가개발 포인트

- 새 예외 코드를 추가할 때는 API 매핑 문서와 실제 라우터 매핑을 함께 갱신해야 한다.
- `cause`와 `metadata`는 디버깅 품질에 직접 영향을 주므로 지나치게 추상적으로 쓰지 않는 편이 낫다.
- 사용자 메시지와 내부 원인을 분리해 두는 현재 구조를 유지하면 운영 로그와 외부 응답을 분리하기 쉽다.

## 4. 관련 문서

- `docs/api/chat.md`
- `docs/api/ui.md`
- `docs/shared/logging.md`
