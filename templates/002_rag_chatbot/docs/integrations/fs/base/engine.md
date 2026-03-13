# BaseFSEngine 가이드

이 문서는 `src/rag_chatbot/integrations/fs/base/engine.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

파일 시스템 엔진 포트를 정의한다.

## 2. 공개 구성

- 클래스 `BaseFSEngine`
  공개 메서드: `name`, `write_text`, `read_text`, `list_files`, `exists`, `mkdir`, `move`, `copy`

## 3. 코드 설명

- 저장소 구현은 로컬 파일 시스템 외의 백엔드를 붙일 때도 이 포트만 만족하면 된다.

## 4. 유지보수/추가개발 포인트

- 이 모듈을 확장할 때는 같은 계층의 이웃 모듈과 계약이 어디에서 맞물리는지 먼저 확인하는 편이 안전하다.

## 5. 관련 문서

- `docs/integrations/overview.md`
