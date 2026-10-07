# 팀 Todo CLI 기술 설계 (TSD)

## 1. 기술 구성

- Python 3.11을 지원한다. 프로젝트의 `.python-version`과 `pyproject.toml` 설정을 따른다.
- Typer를 CLI 프레임워크로 사용하고 `ttodo` 콘솔 명령을 패키지 진입점으로 등록한다.
- HTTP 요청은 런타임 의존성인 HTTPX로 수행한다.
- 기존 FastAPI 서버와 `/api/v1/todos` API 계약을 사용한다. CLI는 실행 시 `/openapi.json`을 조회하거나 서버 스키마로부터 명령을 생성하지 않는다.
- 패키지 메타데이터와 빌드 구성을 추가해 저장소 루트에서 `uvx --from . ttodo`로 실행할 수 있게 한다.

## 2. 설치와 실행

`uv`가 설치된 환경에서 저장소 루트로 이동한 뒤 다음처럼 사용한다.

```sh
uvx --from . ttodo --help
uvx --from . ttodo list
```

`uvx`는 필요한 패키지 실행 환경을 관리한다. 프로젝트 개발 환경에서 바로 확인할 때는 `uv run ttodo --help`를 사용할 수 있다.

서버 실행은 기존 프로젝트 절차를 따른다.

```sh
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

사용 셸에 종속되는 설치 스크립트나 경로 처리는 두지 않는다. PowerShell, Command Prompt, POSIX 셸에서 호환되는 명령 예시를 유지한다.

## 3. 설정

| 설정 | 설명 | 우선순위 |
|---|---|---|
| 기본값 | `http://127.0.0.1:8000` | 가장 낮음 |
| `TEAM_TODO_BASE_URL` | API 서버의 기본 주소를 환경 변수로 지정 | 기본값보다 높음 |
| `--base-url` | 이번 CLI 실행에서 사용할 API 주소 | 환경 변수보다 높음 |

주소에는 호스트와 선택적 포트를 지정한다. CLI가 `/api/v1/todos`를 붙여 요청하므로 주소 끝의 `/`는 허용하고 정규화한다. `/openapi.json` 경로를 입력하는 방식은 지원하지 않는다.

전역 출력 옵션은 명령 앞에 둔다.

```sh
ttodo --json list
ttodo --base-url http://127.0.0.1:8000 list
ttodo --base-url http://127.0.0.1:8000 --json get 12
```

### 도움말 작성 규칙

`ttodo --help`와 `ttodo <command> --help`는 사용자에게 보이는 제품 문구이므로 plain English로 작성한다. 각 도움말은 짧은 문장과 익숙한 단어를 사용한다. 설명 문구에는 `endpoint`, `payload`, `query parameter`, `enum`, `pagination`, `HTTP` 같은 개발자 용어를 넣지 않는다. CLI 옵션명과 API에서 정한 상태·우선순위 값은 인터페이스 이름이므로 그대로 쓰고, 바로 옆 설명은 쉬운 영어로 뜻을 알려준다.

루트 도움말은 한 줄 소개, 명령별 한 줄 설명, 공통 옵션, 최소한의 시작 예시를 포함한다. 각 명령 도움말은 무엇을 하는지, 필요한 입력, 선택 가능한 필드, 기본값 또는 필터 동작, 성공 예시를 포함한다. 옵션은 필수/선택 여부와 입력 형식·허용 값을 설명한다. 도움말만 읽고 사용자가 첫 작업을 실행할 수 있어야 한다.

사용자에게 보이는 영어 설명의 기준 문구:

| 위치 | 도움말 문구 예시 |
|---|---|
| 루트 소개 | `Manage your team's to-do list from the command line.` |
| `create` | `Create a task to remember.` |
| `list` | `Show tasks. You can narrow the list by status, person, priority, due date, or tag.` |
| `get` | `Show all details for one task.` |
| `update` | `Change only the details you provide. Leave out anything you want to keep as it is.` |
| `delete` | `Delete a task permanently. This cannot be undone.` |
| `--title` | `A short name for the task (required when creating a task).` |
| `--description` | `More information about the task.` |
| `--assignee` | `The name of the person responsible for this task.` |
| `--due-date` | `The day the task is due, written as YYYY-MM-DD.` |
| `--priority` | `How important the task is: LOW, MEDIUM, or HIGH. New tasks use MEDIUM.` |
| `--status` | `Where the task stands: TODO, IN_PROGRESS, or DONE. New tasks use TODO.` |
| `--tag` | `A label for grouping tasks. Add this option again to use more than one label.` |
| `--clear-description` | `Remove the task description.` |
| `--clear-assignee` | `Remove the assigned person's name.` |
| `--clear-due-date` | `Remove the due date.` |
| `--clear-tags` | `Remove all labels from the task.` |
| `--due-date-from` | `Show tasks due on or after this day (YYYY-MM-DD).` |
| `--due-date-to` | `Show tasks due on or before this day (YYYY-MM-DD).` |
| `--tag` on `list` | `Show tasks with this label.` |
| `--limit` | `The most tasks to show at once (1–100; default: 50).` |
| `--offset` | `How many tasks to skip before showing results (default: 0).` |
| `--json` | `Print the result as JSON for use with other tools.` |
| `--base-url` | `Use a different Todo server. Default: http://127.0.0.1:8000.` |

Option descriptions for each list filter, the ID argument, and the `--status` and `--priority` filters must follow the same plain-English style. Because `--tag` is used for both adding labels and filtering, its help text must describe the action for that specific command. The CLI may include a short technical alias or exact option name, but must explain the meaning in everyday English.

## 4. 명령 인터페이스와 API 매핑

현재 OpenAPI 애플리케이션 경로에는 다섯 HTTP 작업이 있다. 각 작업은 아래 표의 명령 하나에 대응하며 모두 구현하고 테스트한다. 목록 작업의 각 query parameter도 빠짐없이 대응한다. ID는 양의 정수이며 enum과 날짜는 서버 API에서 허용하는 값과 형식을 사용한다.

| CLI | HTTP 요청 |
|---|---|
| `ttodo create --title TEXT [필드 옵션]` | `POST /api/v1/todos` |
| `ttodo list [필터 옵션]` | `GET /api/v1/todos` |
| `ttodo get ID` | `GET /api/v1/todos/{todo_id}` |
| `ttodo update ID [수정 옵션]` | `PATCH /api/v1/todos/{todo_id}` |
| `ttodo delete ID` | `DELETE /api/v1/todos/{todo_id}` |

FastAPI의 `/docs`, `/redoc`, `/openapi.json`은 문서 경로이지 Todo 작업 API가 아니므로 별도 CLI 명령으로 만들지 않는다.

### 생성과 수정 필드

생성과 수정은 다음 옵션을 사용한다. 필드 이름은 CLI에서 소문자 kebab-case로 쓴다.

| 옵션 | 값 |
|---|---|
| `--title` | 제목 문자열 |
| `--description` | 설명 문자열 |
| `--assignee` | 담당자 문자열 |
| `--due-date` | `YYYY-MM-DD` |
| `--priority` | `LOW`, `MEDIUM`, `HIGH` |
| `--status` | `TODO`, `IN_PROGRESS`, `DONE` |
| `--tag` | 태그 문자열. 여러 번 지정해 태그 목록을 전달 |

`create`에서 `--title`은 필수이고 나머지 필드는 생략할 수 있다. 서버가 정의한 기본값과 검증 규칙을 그대로 적용한다.

`update`에서 일반 필드를 생략하면 요청 본문에서 제외해 기존 값을 유지한다. nullable 필드를 비우려면 각각 `--clear-description`, `--clear-assignee`, `--clear-due-date`를 사용한다. 해당 clear 옵션과 같은 필드의 값 옵션은 동시에 지정할 수 없다. 태그를 지정하면 기존 태그 전체를 교체하고, `--clear-tags`는 태그를 모두 제거한다. 태그 값 옵션과 `--clear-tags`는 함께 지정할 수 없다. 변경 옵션이 없으면 요청을 보내지 않고 CLI 사용 오류를 표시한다.

### 목록 옵션

| 옵션 | API 매개변수 | 설명 |
|---|---|---|
| `--status` | `status` | `TODO`, `IN_PROGRESS`, `DONE` |
| `--assignee` | `assignee` | 담당자 이름 완전 일치 |
| `--priority` | `priority` | `LOW`, `MEDIUM`, `HIGH` |
| `--due-date-from` | `due_date_from` | 포함 마감일 시작 (`YYYY-MM-DD`) |
| `--due-date-to` | `due_date_to` | 포함 마감일 종료 (`YYYY-MM-DD`) |
| `--tag` | `tag` | 태그 이름 필터 |
| `--limit` | `limit` | 1~100, 기본값 50 |
| `--offset` | `offset` | 0 이상, 기본값 0 |

여러 필터를 함께 지정하면 서버가 AND 조건으로 적용한다. 기본 정렬은 생성 시각 내림차순, 동률이면 ID 내림차순이다.

## 5. 출력과 오류 처리

- 기본 텍스트 출력은 목록에서 ID, 제목, 상태, 우선순위, 담당자, 마감일을 한눈에 비교할 수 있게 표시한다. 단건 응답은 필드 이름과 값을 읽기 쉬운 형태로 표시한다.
- `--json`은 API 결과 JSON을 표준 출력에 출력한다. 목록은 `{ "items": [...], "limit": ..., "offset": ... }` 응답 구조를 유지한다. `204` 삭제 응답은 성공 메시지를 JSON 모드에서 JSON 문자열로 출력하지 않으며 표준 출력은 비운다.
- 진행/오류 안내는 표준 오류 출력으로 보낸다. `--json` 실행에서는 표준 출력이 결과 JSON 외 텍스트를 포함하지 않게 한다.
- API 오류는 HTTP 상태와 서버의 `detail`을 사용자에게 읽기 쉽게 표시한다. 네트워크 연결 실패는 서버 주소와 서버 실행 여부를 확인하도록 안내한다.
- 내부 예외의 traceback은 기본 사용자 출력에 노출하지 않는다.
- 종료 코드는 성공 `0`, 서버·네트워크 오류 `1`, CLI 인수 또는 입력 오류 `2`로 한다.

## 6. 예시

```sh
ttodo create --title "회의 자료 준비" --assignee "민지" --due-date 2026-10-15 --priority HIGH --tag 기획 --tag 회의
ttodo list --status TODO --assignee "민지" --limit 20
ttodo --json list --tag 출시 --offset 0
ttodo get 1
ttodo update 1 --status DONE
ttodo update 1 --clear-assignee --tag 완료
ttodo delete 1
```

## 7. 테스트 및 품질

- 빠른 CLI 테스트는 HTTP 응답을 대체해 개발 서버나 개발 DB 없이 검증한다. 별도 E2E 테스트는 임시 SQLite DB와 로컬 API 서버를 사용한다.
- 명령별 요청 메서드·경로·쿼리·본문, 출력, 종료 코드를 확인한다.
- CLI 패키지 진입점 및 `uvx --from . ttodo --help` 실행 가능성을 검증한다.
- Python 품질 기준과 전체 게이트는 저장소 `AGENTS.md` 및 `./scripts/check.sh`를 따른다.

빠른 CLI 자동화 테스트는 `tests/test_cli.py`에서 HTTPX 응답을 대체해 실행한다: `uv run --locked pytest tests/test_cli.py`. 실제 CLI 프로세스와 API·임시 SQLite DB를 잇는 E2E 테스트는 `uv run --locked pytest tests/test_cli_e2e.py`로 실행한다. 저장소 전체 품질 게이트는 `./scripts/check.sh`다. `uvx --from . ttodo --help`로 로컬 패키징 진입점을 확인한다.
