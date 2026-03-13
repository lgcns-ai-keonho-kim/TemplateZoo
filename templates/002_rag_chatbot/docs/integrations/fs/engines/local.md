# LocalFSEngine 가이드

이 문서는 `src/rag_chatbot/integrations/fs/engines/local.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

로컬 파일 시스템 기반 엔진 구현체다.

## 2. 공개 구성

- 클래스 `LocalFSEngine`
  공개 메서드: `name`, `write_text`, `read_text`, `list_files`, `exists`, `mkdir`, `move`, `copy`

## 3. 코드 설명

- 현재 구현은 소스 파일의 공개 메서드와 인접 모듈 협업을 기준으로 읽는 것이 가장 안전하다.

## 4. 유지보수/추가개발 포인트

- 이 모듈을 확장할 때는 같은 계층의 이웃 모듈과 계약이 어디에서 맞물리는지 먼저 확인하는 편이 안전하다.

## 5. 관련 문서

- `docs/integrations/overview.md`
