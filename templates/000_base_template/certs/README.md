# CERTS 관리 가이드

이 폴더는 로컬 개발 환경에서 사용할 인증서/키 파일을 보관하기 위한 공간입니다.
보안상 **인증서 및 키 파일은 Git에 커밋하지 않습니다.**

## 기본 원칙

- 이 폴더의 실제 인증서 파일은 **로컬에서만 관리**합니다.
- `certs/*`는 `.gitignore`로 무시하고, 문서만 예외로 관리합니다.
- 파일 권한은 **최소 권한(읽기)** 으로 유지합니다.

## 권장 .gitignore 설정

```gitignore
certs/*
!certs/README.md
```

## 파일 배치 예시

- `certs/http_ca.crt` (Elasticsearch CA 인증서)
- `certs/ca.pem`
- `certs/client.crt`
- `certs/client.key`

## Elasticsearch CA 인증서 예시

서버가 `/etc/elasticsearch/certs/http_ca.crt`에 CA를 두는 경우:

```bash
sudo cp /etc/elasticsearch/certs/http_ca.crt certs/http_ca.crt
sudo chown $USER:$USER certs/http_ca.crt
chmod 644 certs/http_ca.crt
```

이후 파이썬 클라이언트에서 다음처럼 사용합니다.

```python
Elasticsearch(
    "https://127.0.0.1:9200",
    basic_auth=("<USER_NAME>", "<PASSWORD>"),
    ca_certs="certs/http_ca.crt",
    verify_certs=True,
)
```

## 권한 팁

- 복사가 어려우면 ACL로 읽기 권한만 부여할 수 있습니다.

```bash
sudo setfacl -m u:$USER:r /etc/elasticsearch/certs/http_ca.crt
```

## 운영 가이드

- 인증서가 갱신되면 파일을 교체하고 관련 환경 변수 경로를 확인합니다.
- 유출 의심 시 즉시 폐기하고 재발급 후 재배포합니다.
- 키 파일(`*.key`)은 특히 민감하므로 권한을 `600`으로 제한하세요.
