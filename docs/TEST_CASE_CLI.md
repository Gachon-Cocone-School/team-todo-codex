# 팀 Todo CLI 테스트 케이스

## 공통 기준

- CLI 이름: `ttodo`
- 기본 API 주소: `http://127.0.0.1:8000`
- API prefix: `/api/v1`
- 기본 출력은 읽기 쉬운 text이며 `--json`은 명령 앞에 지정한다.
- 빠른 CLI 테스트는 HTTP 응답을 대체해 실행하고 개발 DB를 변경하지 않는다.
- CLI E2E 테스트는 임시 SQLite DB와 로컬 API 서버를 사용하며 개발 DB를 변경하지 않는다.
- 각 케이스는 독립 실행 가능해야 한다. ID는 테스트가 준비한 Todo ID를 뜻한다.
- 플랫폼 검증 대상은 macOS, Linux, Windows이며, 문서화된 명령은 POSIX 셸 및 PowerShell에서 사용할 수 있어야 한다.
- `tests/test_cli.py`는 HTTP 응답을 대체해 요청 매핑과 CLI 동작을 빠르게 확인한다. 각 query parameter는 독립 테스트와 복합 필터 테스트로 확인한다.
- `tests/test_cli_e2e.py`는 `uv run --locked ttodo`를 실제 subprocess로 실행해 로컬 API 서버와 임시 SQLite DB까지 검증한다.

## 실제 서버 E2E 실행

- **Command:** `uv run --locked pytest tests/test_cli_e2e.py`
- 테스트는 임시 디렉터리에 SQLite DB를 만들고 Alembic 마이그레이션을 적용한 뒤, 임의의 로컬 포트에서 API 서버를 실행한다.
- 서버 준비 후 실제 `ttodo` 명령으로 생성, 복합 필터 목록, JSON 단건 조회, 부분 수정, nullable 필드 비우기, 태그 교체, 삭제를 검증한다.
- 잘못된 날짜 입력이 로컬에서 종료 코드 `2`로 거부되는지, 존재하지 않는 항목과 연결할 수 없는 서버가 종료 코드 `1` 및 traceback 없는 오류를 내는지 확인한다.
- 테스트 종료 시 API 프로세스를 정리하고 임시 DB를 삭제한다. 개발 DB는 사용하지 않는다.
- 전체 품질 게이트는 `./scripts/check.sh`로 실행한다.

## 성공 케이스

### TC-CLI-S01 — 도움말 표시

- [ ] **Command:** `ttodo --help`
- [ ] **Expected:** 종료 코드 `0`; `create`, `list`, `get`, `update`, `delete`와 전역 옵션 설명을 확인할 수 있다.

### TC-CLI-S02 — 로컬 저장소에서 uvx 실행

- [ ] **Command:** 저장소 루트에서 `uvx --from . ttodo --help`
- [ ] **Expected:** 지원 macOS, Linux, Windows 환경에서 패키지를 실행하고 도움말을 출력한다.

### TC-CLI-S03 — 기본값으로 Todo 생성

- [ ] **Command:** `ttodo create --title "회의 자료 준비"`
- [ ] **Expected request:** `POST /api/v1/todos`, 본문에 제목을 전달한다.
- [ ] **Expected output:** 종료 코드 `0`; 생성 결과가 기본 text로 표시된다.

### TC-CLI-S04 — 선택 필드와 여러 태그를 포함해 생성

- [ ] **Command:** `ttodo create --title "출시 점검" --description "배포 전 확인" --assignee "민지" --due-date 2026-10-15 --priority HIGH --status IN_PROGRESS --tag 출시 --tag 검토`
- [ ] **Expected request:** `POST /api/v1/todos`; 두 태그를 포함해 필드들을 API JSON 본문으로 전달한다.
- [ ] **Expected output:** 생성 응답의 텍스트를 사람이 읽을 수 있게 표시한다.

### TC-CLI-S05 — 목록 기본 조회 및 페이지 응답

- [ ] **Command:** `ttodo list`
- [ ] **Expected request:** `GET /api/v1/todos?limit=50&offset=0`.
- [ ] **Expected output:** 종료 코드 `0`; 결과가 없으면 빈 목록임을 알리고, 있으면 ID·제목·상태 등 주요 항목을 표시한다.

### TC-CLI-S06 — 여러 목록 필터와 페이지네이션

- [ ] **Command:** `ttodo list --status DONE --assignee "민지" --priority HIGH --due-date-from 2026-10-01 --due-date-to 2026-10-31 --tag 출시 --limit 2 --offset 1`
- [ ] **Expected request:** 모든 옵션을 대응하는 API query parameter로 전달한다.
- [ ] **Expected output:** 전달한 limit/offset으로 조회된 항목을 표시한다.

### TC-CLI-S07 — Todo 단건 조회

- [ ] **Command:** `ttodo get 1`
- [ ] **Expected request:** `GET /api/v1/todos/1`.
- [ ] **Expected output:** 모든 응답 필드와 태그를 읽기 쉬운 형태로 표시한다.

### TC-CLI-S08 — 전달한 필드만 수정

- [ ] **Command:** `ttodo update 1 --status DONE --priority LOW`
- [ ] **Expected request:** `PATCH /api/v1/todos/1`; 지정한 필드만 본문에 포함한다.
- [ ] **Expected output:** 수정된 Todo를 표시한다.

### TC-CLI-S09 — nullable 필드 비우기와 태그 교체·제거

- [ ] **Commands:** `ttodo update 1 --clear-assignee --clear-due-date`, `ttodo update 1 --tag 완료`, `ttodo update 1 --clear-tags`
- [ ] **Expected request:** nullable 필드에는 명시적 `null`, 태그 지정에는 새 태그 배열, clear-tags에는 빈 배열을 전달한다.
- [ ] **Expected:** 옵션 동작은 각각 독립적으로 검증하며 PATCH에서 다른 필드는 생략한다.

### TC-CLI-S10 — Todo 삭제

- [ ] **Command:** `ttodo delete 1`
- [ ] **Expected request:** `DELETE /api/v1/todos/1`.
- [ ] **Expected output:** 확인 프롬프트 없이 종료 코드 `0`; 삭제 성공 안내를 text 모드에 표시한다.

### TC-CLI-S11 — JSON 목록 출력

- [ ] **Command:** `ttodo --json list --limit 2`
- [ ] **Expected output:** 표준 출력은 유효한 JSON이며 API 페이지 구조 `{ "items": [...], "limit": 2, "offset": 0 }`를 유지한다. 안내 문구는 표준 출력에 섞이지 않는다.

### TC-CLI-S12 — JSON 단건·생성·수정 출력

- [ ] **Commands:** `ttodo --json get 1`, `ttodo --json create --title "JSON 확인"`, `ttodo --json update 1 --status DONE`
- [ ] **Expected output:** 결과가 있는 각 명령은 JSON 객체를 표준 출력으로 출력하고 성공 종료 코드 `0`을 반환한다.

### TC-CLI-S13 — JSON 삭제 결과

- [ ] **Command:** `ttodo --json delete 1`
- [ ] **Expected output:** 성공 종료 코드 `0`; HTTP `204` 응답에 대응해 표준 출력은 비어 있고 임의의 JSON 결과를 만들지 않는다.

### TC-CLI-S14 — API 주소 재정의

- [ ] **Commands:** `ttodo --base-url http://localhost:9000 list`; `TEAM_TODO_BASE_URL=http://localhost:9000` 설정 후 `ttodo list`
- [ ] **Expected request:** 지정된 주소의 `/api/v1/todos`로 요청한다. 명령행 옵션과 환경 변수를 함께 지정하면 `--base-url`이 우선한다.

## 실패 케이스

### TC-CLI-F01 — 필수 제목 누락

- [ ] **Command:** `ttodo create`
- [ ] **Expected:** 종료 코드 `2`; 사용법과 `--title` 필수 오류를 표시하고 HTTP 요청을 보내지 않는다.

### TC-CLI-F02 — 수정할 필드 없음

- [ ] **Command:** `ttodo update 1`
- [ ] **Expected:** 종료 코드 `2`; 수정 필드가 필요하다는 안내를 표시하고 요청을 보내지 않는다.

### TC-CLI-F03 — 충돌하는 clear 옵션

- [ ] **Command:** `ttodo update 1 --assignee 민지 --clear-assignee`
- [ ] **Expected:** 종료 코드 `2`; 충돌 옵션을 안내하고 요청을 보내지 않는다.

### TC-CLI-F04 — 잘못된 CLI 입력

- [ ] **Commands:** 잘못된 enum, 날짜 형식, ID, `limit=101`, 음수 offset을 지정한다.
- [ ] **Expected:** 인수 자체를 CLI가 검증할 수 있는 경우 종료 코드 `2`와 간단한 입력 오류를 표시한다. 서버 검증 대상은 API의 `422` 오류를 이해하기 쉽게 전달한다.

### TC-CLI-F05 — 역전된 마감일 범위

- [ ] **Command:** `ttodo list --due-date-from 2026-10-31 --due-date-to 2026-10-01`
- [ ] **Expected:** 종료 코드 `2` 또는 서버 `422`를 사용자에게 명확히 설명한다. 잘못된 범위로 성공 결과를 출력하지 않는다.

### TC-CLI-F06 — 존재하지 않는 Todo

- [ ] **Commands:** `ttodo get 999999`, `ttodo update 999999 --status DONE`, `ttodo delete 999999`
- [ ] **Expected:** 종료 코드 `1`; API `404`와 리소스를 찾을 수 없다는 안내를 표시한다.

### TC-CLI-F07 — 서버 연결 실패

- [ ] **Command:** 실행 중인 서버가 없는 주소에 `ttodo --base-url http://127.0.0.1:9 list`를 실행한다.
- [ ] **Expected:** 종료 코드 `1`; traceback 대신 서버 주소와 서버 실행 여부를 확인하라는 안내를 표시한다.

### TC-CLI-F08 — 서버 오류 응답

- [ ] **Setup:** API가 `409`, `422`, `500` 응답을 반환한다.
- [ ] **Expected:** 종료 코드 `1`; 상태 코드와 안전한 API 오류 내용을 표시하고 성공 결과 형식으로 응답하지 않는다. 내부 traceback은 노출하지 않는다.

## 교차 플랫폼 확인

- [ ] macOS와 Linux에서 저장소 루트 기준 `uvx --from . ttodo --help`와 대표 CRUD 명령을 실행한다.
- [ ] Windows PowerShell에서 동일한 CLI 패키지가 실행되고 옵션 인수와 날짜가 정상 전달되는지 확인한다.
- [ ] Windows Command Prompt에서도 도움말과 목록 명령을 실행한다.
- [ ] 테스트와 문서 예시는 셸별 환경 변수 설정 문법을 구분해 안내하며, CLI 자체 동작은 셸 기능에 의존하지 않는다.

## OpenAPI 엔드포인트 커버리지

모든 애플리케이션 경로와 동사는 대응하는 CLI 명령, 성공 사례, 실패 사례가 있어야 한다. 이 표를 기준으로 OpenAPI가 바뀔 때 테스트 문서도 갱신한다.

| OpenAPI 작업 | CLI 명령 | 성공 검증 | 실패 검증 |
|---|---|---|---|
| `POST /api/v1/todos` → `201` | `create` | TC-CLI-S03, S04 | TC-CLI-F01, F04, F08 |
| `GET /api/v1/todos` → `200` | `list` | TC-CLI-S05, S06, S14 | TC-CLI-F04, F05, F07, F08 |
| `GET /api/v1/todos/{todo_id}` → `200` | `get` | TC-CLI-S07 | TC-CLI-F06, F07, F08 |
| `PATCH /api/v1/todos/{todo_id}` → `200` | `update` | TC-CLI-S08, S09 | TC-CLI-F02, F03, F04, F06, F08 |
| `DELETE /api/v1/todos/{todo_id}` → `204` | `delete` | TC-CLI-S10 | TC-CLI-F06, F07, F08 |

`GET /api/v1/todos`의 query parameter 각각도 요청에 정확히 전달되는지 검사한다: `status`, `assignee`, `priority`, `due_date_from`, `due_date_to`, `tag`, `limit`, `offset`. 단일 복합 필터 테스트만으로 개별 매핑을 대체하지 않는다. 각 매개변수를 독립적으로 확인하고, 여러 조건을 함께 썼을 때 모두 전달되는지도 확인한다. 문서 경로 `/docs`, `/redoc`, `/openapi.json`은 애플리케이션 동작 경로가 아니므로 CLI 엔드포인트 커버리지에 포함하지 않는다.

## 도움말 문구 검증

### TC-CLI-S15 — 루트 도움말은 쉬운 영어로 제공

- [ ] **Command:** `ttodo --help`
- [ ] **Expected:** plain English 한 줄 소개와 다섯 명령 설명, 공통 옵션(`--base-url`, `--json`) 및 시작 예시를 표시한다.
- [ ] 각 설명은 일상적인 단어로 쓰며 `endpoint`, `payload`, `query parameter`, `enum`, `pagination`, `HTTP` 같은 개발 용어를 사용자 설명으로 노출하지 않는다.

### TC-CLI-S16 — 각 명령 도움말은 사용에 필요한 설명을 제공

- [ ] **Commands:** `ttodo create --help`, `ttodo list --help`, `ttodo get --help`, `ttodo update --help`, `ttodo delete --help`
- [ ] **Expected:** 각 출력이 plain English이며 명령의 목적, 필수·선택 입력, 허용 값이나 형식, 동작 기본값, 실제 실행 예시를 설명한다.
- [ ] `list --help`는 상태·담당자·우선순위·마감일·태그와 페이지 크기·시작 위치 필터를 빠짐없이 설명한다.
- [ ] `update --help`는 생략한 항목은 유지된다는 점, 값을 비우는 clear 옵션, 태그 교체·전체 제거 동작을 설명한다.
- [ ] `delete --help`는 영구 삭제를 알리고, `create --help`는 제목이 필요함을 알린다.

### TC-CLI-S17 — 도움말 예시는 그대로 실행 가능한 형식

- [ ] **Expected:** 루트 및 명령별 도움말에 표시되는 각 예시가 문서화된 옵션과 문법을 사용한다.
- [ ] 최소 하나의 생성, 목록, 단건 조회, 수정, 삭제 예시를 각각 제공한다.
- [ ] 예시가 여러 셸에서 다르게 해석되는 인용·환경변수 구문에 의존하지 않는다.

## 명령별 전체 입력 필드 커버리지

### TC-CLI-S18 — 수정 가능한 모든 필드 전달

- [ ] **Command:** `ttodo update 1 --title "새 제목" --description "설명" --assignee "민지" --due-date 2026-10-15 --priority HIGH --status IN_PROGRESS --tag 출시 --tag 검토`
- [ ] **Expected request:** `PATCH /api/v1/todos/1`; 지정한 필드를 모두 API 필드명으로 변환해 전송하고 태그 목록을 교체한다.
- [ ] **Expected:** 생략 필드는 본문에 포함하지 않아 서버 기존 값을 보존한다.

### TC-CLI-S19 — 각 목록 필터를 독립 매핑

- [ ] `--status DONE`은 `status=DONE`으로 전달한다.
- [ ] `--assignee "민지"`는 `assignee=민지`로 전달한다.
- [ ] `--priority HIGH`는 `priority=HIGH`로 전달한다.
- [ ] `--due-date-from 2026-10-01`과 `--due-date-to 2026-10-31`은 각 날짜 query parameter로 전달한다.
- [ ] `--tag 출시`는 `tag=출시`로 전달한다.
- [ ] `--limit 2`와 `--offset 1`은 각각 같은 이름의 숫자 query parameter로 전달한다.
- [ ] 생략된 필터는 요청에서 생략하고, 복합 필터는 지정된 값을 모두 전달한다.

### TC-CLI-S20 — 모든 명령의 JSON 모드

- [ ] **Commands:** `ttodo --json create --title "JSON 확인"`, `ttodo --json list`, `ttodo --json get 1`, `ttodo --json update 1 --status DONE`, `ttodo --json delete 1`
- [ ] **Expected:** 모든 성공 응답에서 표준 출력은 JSON 결과만 포함한다. DELETE `204`는 표준 출력을 비운다. 오류 메시지는 표준 오류로 보낸다.
