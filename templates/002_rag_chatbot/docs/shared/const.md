# Shared Const 가이드

이 문서는 `src/rag_chatbot/shared/const/__init__.py`가 제공하는 공통 상수의 의미를 설명한다.

## 1. 현재 상수 역할

- 기본 텍스트 인코딩
- 환경 변수 중첩 구분자
- 여러 공통 유틸리티가 함께 사용하는 소규모 전역 값

## 2. 유지보수/추가개발 포인트

- 상수는 여러 계층이 공유하므로, 개별 기능 전용 값까지 여기에 넣기 시작하면 책임이 흐려진다.
- 환경 변수 파싱 규칙에 영향을 주는 상수는 `docs/shared/config.md`와 함께 갱신하는 편이 좋다.

## 3. 관련 문서

- `docs/shared/config.md`
- `docs/shared/overview.md`
