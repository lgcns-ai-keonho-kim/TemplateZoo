# FileLogRepository 가이드

이 문서는 `src/rag_chatbot/integrations/fs/file_repository.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

파일 기반 로그 저장소다. 날짜별 디렉터리와 UUID 로그 파일 규칙을 사용한다.

## 2. 공개 구성

- 클래스 `FileLogRepository`
  공개 메서드: `base_dir`, `add`, `list`

## 3. 코드 설명

- 기본 저장 형식은 JSON 문자열이며, 손상된 로그 파일은 경고 레코드로 복구해 목록에 포함한다.
- 파일 경로는 `YYYYMMDD/<uuid>.log` 규칙으로 생성된다.

## 4. 유지보수/추가개발 포인트

- 파일 포맷을 바꾸면 기존 손상 로그 복구 경로와 정렬 기준도 함께 점검해야 한다.
- 대량 로그 환경에서는 날짜 디렉터리 보관 정책과 파일 수 관리 정책을 추가로 설계하는 편이 좋다.

## 5. 관련 문서

- `docs/integrations/overview.md`
