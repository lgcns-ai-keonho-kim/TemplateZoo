# 공통 상수 가이드

이 문서는 `src/base_template/shared/const/__init__.py`의 상수 집합을 설명합니다.

**목적**

- 프로젝트 전역에서 재사용되는 기본 상수를 한 곳에서 관리합니다.
- 설정 로더와 파일 처리 로직의 기준값을 통일합니다.

**상수 목록**

- `SharedConst.DEFAULT_ENCODING`: 기본 파일 인코딩
- `SharedConst.DEFAULT_TIMEZONE`: 기본 타임존 이름
- `SharedConst.ENV_NESTED_DELIMITER`: 환경 변수 중첩 구분자

**사용 예시**

```python
from base_template.shared.const import SharedConst

print(SharedConst.DEFAULT_ENCODING)
```

**운영 팁**

- 환경 변수 규칙 변경이 필요하면 `ENV_NESTED_DELIMITER`를 기준으로 전역 변경합니다.
- 인코딩 기본값은 설정 로더와 파일 저장소에서 함께 사용됩니다.
