# 설정 로더 명세

이 문서는 `src/base_template/shared/config/loader.py`의 `ConfigLoader` 동작 계약을 정의한다.

## 역할

`ConfigLoader`는 다중 설정 소스를 수집하고 병합해 최종 설정 딕셔너리를 생성한다.

- 소스 타입: `dict`, JSON 파일, 환경 변수
- 병합 정책: 뒤에 추가된 소스가 우선
- 출력 타입: `dict[str, Any]`

## 소스 API

| 메서드 | 입력 | 동작 |
| --- | --- | --- |
| `add_dict` | `Mapping` | 입력 딕셔너리를 소스 목록에 추가 |
| `add_json_file` | `path`, `required`, `encoding` | JSON 파일 로드 후 소스 추가 |
| `add_env` | `prefix`, `delimiter`, `lowercase_keys` | 환경 변수를 중첩 dict로 변환해 소스 추가 |
| `build` | `overrides` | 누적 소스 + 오버라이드 병합 결과 반환 |

## 병합 규칙

1. `build`는 소스 등록 순서대로 병합한다.
2. 동일 키 충돌 시 나중 소스 값이 이전 값을 덮어쓴다.
3. 두 값이 모두 dict인 경우 재귀 병합한다.
4. `overrides`는 최종 단계에서 마지막으로 병합된다.

## 환경 변수 파싱 규칙

- 기본 구분자: `SharedConst.ENV_NESTED_DELIMITER` (`__`)
- `APP__DB__HOST=127.0.0.1` -> `{"app": {"db": {"host": "127.0.0.1"}}}`
- 기본 키 정규화: 소문자 변환

값 파싱:

- `true/false` -> `bool`
- `null/none` -> `None`
- 정수/실수 문자열 -> 숫자
- JSON 문자열(`{...}`, `[...]`) -> `dict`/`list`
- 나머지 -> `str`

## 예외 규칙

1. `path`가 비어 있으면 `ValueError`
2. `required=True` 파일이 없으면 `FileNotFoundError`
3. JSON 파싱 실패 또는 최상위 객체 위반 시 `ValueError`

## 의존성

```text
shared/config/loader
  -> shared/const
  -> shared/logging
```

## 예시

```python
from base_template.shared.config.loader import ConfigLoader

config = (
    ConfigLoader()
    .add_json_file("config/app.json", required=False)
    .add_env(prefix="APP__")
    .build(overrides={"app": {"debug": True}})
)
```
