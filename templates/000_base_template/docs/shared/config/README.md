# 설정 로더 가이드

이 문서는 `src/base_template/shared/config/loader.py`의 `ConfigLoader` 사용 방법을 설명합니다.

**목적**
- 딕셔너리, JSON 파일, 환경 변수를 병합해 하나의 설정 객체를 생성합니다.
- 일관된 키 구조와 기본 타입 파싱을 제공합니다.

**구성 요소**
- 클래스: `ConfigLoader`
- 기본 상수: `SharedConst.DEFAULT_ENCODING`, `SharedConst.ENV_NESTED_DELIMITER`

**병합 규칙**
- 추가된 순서대로 병합되며, 뒤에 온 값이 우선합니다.
- `build(overrides=...)`에 전달한 값이 최종 우선순위를 가집니다.

**환경 변수 규칙**
- 기본 구분자는 `__` 입니다.
- 예시: `APP__DB__HOST=localhost` → `{"app": {"db": {"host": "localhost"}}}`
- 기본적으로 키는 소문자로 변환됩니다.

**기본 사용법**

```python
from base_template.shared.config.loader import ConfigLoader

loader = ConfigLoader()
config = (
    loader
    .add_json_file("config/app.json", required=False)
    .add_env(prefix="APP__")
    .build(overrides={"app": {"debug": True}})
)
```

**딕셔너리 병합**

```python
loader = ConfigLoader()
config = loader.add_dict({"app": {"name": "demo"}}).build()
```

**환경 변수 타입 파싱**
- `true/false`는 불리언으로 변환됩니다.
- `null/none`은 `None`으로 변환됩니다.
- 숫자 문자열은 정수 또는 실수로 변환됩니다.
- JSON 형태 문자열은 객체/배열로 파싱됩니다.

```python
# 예시 환경 변수
# APP__LIMIT=10
# APP__RATIO=0.5
# APP__ENABLED=true
# APP__FEATURES=["a","b"]
```

**주의 사항**
- JSON 파일의 최상위는 반드시 객체여야 합니다.
- 잘못된 JSON은 `ValueError`를 발생시킵니다.
