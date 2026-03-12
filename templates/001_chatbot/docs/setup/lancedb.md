# LanceDB 구성 레퍼런스

이 문서는 `src/chatbot/integrations/db/engines/lancedb`를 사용할 때의 코드 구조와 확장 포인트를 정리한다.
현재 채팅 기본 런타임은 LanceDB를 자동으로 조립하지 않는다.

## 1. 현재 코드 위치

- `src/chatbot/integrations/db/engines/lancedb/engine.py`
- `src/chatbot/integrations/db/engines/lancedb/document_mapper.py`
- `src/chatbot/integrations/db/engines/lancedb/filter_engine.py`
- `src/chatbot/integrations/db/engines/lancedb/schema_adapter.py`

## 2. 사용 목적

1. 로컬 벡터 저장소가 필요할 때 선택할 수 있다.
2. `CollectionSchema` 기반 정의와 벡터 필드 차원 정보를 이용해 검색을 수행한다.
3. 기본 채팅 이력 저장소 대체보다는 벡터 검색용 보조 엔진으로 보는 편이 맞다.

## 3. 환경 변수

```env
LANCEDB_URI=data/db/vector
```

## 4. 유지보수 포인트

1. 차원 수, vector 필드명, payload 매핑 규칙은 스키마와 문서를 함께 유지해야 한다.
2. 필터 후처리 순서를 바꾸면 검색 정확도와 비용이 동시에 바뀔 수 있다.
3. 기본 런타임 비활성 기능이므로, 실제 서비스에 도입할 때는 조립 코드와 장애 대응 문서를 같이 추가해야 한다.

## 5. 추가 개발과 확장 시 주의점

1. 검색 결과를 채팅 런타임에 연결하려면 별도 저장소/서비스 조립이 필요하다.
2. 임베딩 차원이나 거리 기준을 바꾸면 기존 저장 데이터 재적재 여부를 먼저 검토해야 한다.

## 6. 관련 문서

- `docs/integrations/db/engines/lancedb/engine.md`
- `docs/integrations/db/overview.md`
- `docs/setup/env.md`
