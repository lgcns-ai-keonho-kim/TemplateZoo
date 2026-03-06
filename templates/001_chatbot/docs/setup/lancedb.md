# LanceDB 벡터 검색 구성 레퍼런스

이 문서는 LanceDB를 벡터 검색 엔진으로 준비하고 검증하는 절차를 정리한다.
현재 프로젝트에서 SQLite는 벡터 검색을 지원하지 않으므로, 로컬 벡터 검색 기본 경로는 LanceDB를 권장한다.

## 1. 적용 범위

1. 로컬 벡터 검색 실험/검증
2. 임베딩 생성 후 벡터 upsert/search 흐름 점검
3. LanceDB 저장 경로/권한 관리

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/chatbot/integrations/db/engines/lancedb/engine.py` | LanceDB 엔진 구현 |
| `src/chatbot/integrations/db/engines/lancedb/schema_adapter.py` | 스키마/테이블 변환 |
| `src/chatbot/integrations/db/engines/lancedb/filter_engine.py` | 필터 처리 |
| `tests/integrations/db/Vector/test_lancedb_engine_vector.py` | 벡터 검색 검증 테스트 |

## 3. 환경 변수

```env
LANCEDB_URI=data/db/vector
```

설명:

1. `LANCEDB_URI`는 LanceDB 데이터 저장 위치다.
2. 운영/CI에서는 절대경로를 권장한다.

## 4. 준비 절차

1. 디렉터리 준비:

```bash
mkdir -p "$LANCEDB_URI"
ls -ld "$LANCEDB_URI"
```

2. 임베딩 의존 확인(예: Ollama 사용 시):

```bash
curl -sS http://127.0.0.1:11434/api/tags | head
```

기대 결과:

1. LanceDB 경로가 쓰기 가능해야 한다.
2. 임베딩 공급자가 정상 응답해야 벡터 테스트가 동작한다.

## 5. 벡터 검색 동작 요약

1. 컬렉션 생성 시 `vector_field`, `vector_dimension`을 정의한다.
2. 문서 upsert 시 벡터를 함께 저장한다.
3. `VectorSearchRequest`로 `top_k` 검색을 수행한다.

## 6. 실무 점검 포인트

1. 임베딩 차원(`dimension`)과 스키마 차원이 일치해야 한다.
2. 테스트 데이터는 최소 2건 이상으로 유사도 순서가 검증 가능해야 한다.
3. 검색 정확도 검증 시 질의 벡터 생성 모델과 저장 벡터 생성 모델을 동일하게 유지한다.

## 7. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| 벡터 검색 결과가 비어 있음 | 임베딩 생성 실패 또는 upsert 누락 | 테스트 로그, upsert 코드 | 임베딩 응답/저장 문서 재확인 |
| 차원 불일치 오류 | 스키마 차원과 임베딩 차원 불일치 | `vector_dimension`, 임베딩 길이 | 스키마/모델 차원 통일 |
| 파일 접근 오류 | LanceDB 경로 권한 부족 | `LANCEDB_URI`, OS 권한 | 디렉터리 권한 수정 |

## 8. 관련 문서

- `docs/setup/env.md`
- `docs/setup/sqlite.md`
- `docs/integrations/db/overview.md`
