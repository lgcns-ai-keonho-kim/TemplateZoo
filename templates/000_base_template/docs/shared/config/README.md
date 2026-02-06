# 설정 로더 가이드

이 문서는 `src/base_template/shared/config/loader.py`의 `ConfigLoader` 사용 방법을 설명합니다.

**목적**

- 딕셔너리, JSON 파일, 환경 변수를 병합해 하나의 설정 객체를 생성합니다.
- 일관된 키 구조와 기본 타입 파싱 규칙을 제공합니다.
- 로거를 주입해 로딩 과정을 추적할 수 있습니다.

**구성 요소**

- 클래스: `ConfigLoader`
- 기본 상수: `SharedConst.DEFAULT_ENCODING`, `SharedConst.ENV_NESTED_DELIMITER`

## 기본 사용 흐름

1. 소스를 `add_dict`, `add_json_file`, `add_env`로 등록합니다.
2. `build(overrides=...)`로 최종 설정을 생성합니다.
3. 동일 키는 **뒤에 추가된 소스가 우선**합니다.

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

## 딕셔너리 병합

```python
loader = ConfigLoader()
config = loader.add_dict({"app": {"name": "demo"}}).build()
```

## 환경 변수 규칙

- 기본 구분자는 `__` 입니다.
- 예시: `APP__DB__HOST=localhost` → `{"app": {"db": {"host": "localhost"}}}`
- 기본적으로 키는 소문자로 변환됩니다 (`lowercase_keys=True`).

```python
loader = ConfigLoader().add_env(prefix="APP__", delimiter="__", lowercase_keys=True)
```

## 환경 변수 타입 파싱

- `true/false` → `bool`
- `null/none` → `None`
- 숫자 문자열 → `int` 또는 `float`
- JSON 문자열 → `dict`/`list`

```bash
# 예시 환경 변수
# APP__LIMIT=10
# APP__RATIO=0.5
# APP__ENABLED=true
# APP__FEATURES=["a","b"]
```

## 주의 사항

- JSON 파일의 최상위는 반드시 객체여야 합니다.
- 잘못된 JSON은 `ValueError`를 발생시킵니다.
- `required=True`로 설정하면 파일이 없을 때 예외가 발생합니다.
