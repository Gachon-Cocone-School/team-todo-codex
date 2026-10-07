# Team Todo CLI 사용 설명서

`ttodo` 명령으로 실행 중인 Team Todo API에 할 일을 등록하고 관리할 수 있습니다. 이 안내서는 저장소 루트에서 `uv`가 설치되어 있다고 가정합니다.

## 시작하기

먼저 API 서버를 준비합니다. 서버를 한 번만 설치·초기화하면 이후에는 서버 실행만 하면 됩니다.

```sh
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1
```

서버를 실행한 터미널을 열어 두고, 저장소 루트에서 새 터미널을 열어 CLI를 사용합니다.

```sh
uvx --from . ttodo --help
```

`uvx`는 CLI 실행에 필요한 환경을 준비합니다. 이미 개발 환경을 동기화했다면 모든 예시에서 `uvx --from . ttodo` 대신 `uv run ttodo`를 사용할 수 있습니다.

## 할 일 만들기

제목은 필수입니다. 담당자, 마감일, 우선순위, 상태, 태그는 선택 사항입니다. 기본 우선순위는 `MEDIUM`, 기본 상태는 `TODO`입니다. 날짜는 `YYYY-MM-DD` 형식으로 입력합니다.

```sh
uvx --from . ttodo create --title "회의 자료 준비" --assignee "민지" --due-date 2026-10-15 --priority HIGH --tag 기획 --tag 회의
```

태그를 여러 개 지정하려면 `--tag`를 각 태그 앞에 반복합니다. 사용할 수 있는 우선순위는 `LOW`, `MEDIUM`, `HIGH`이고 상태는 `TODO`, `IN_PROGRESS`, `DONE`입니다.

## 할 일 찾기

목록을 보려면 `list`, 한 항목의 전체 내용을 보려면 `get`과 할 일 ID를 사용합니다.

```sh
uvx --from . ttodo list
uvx --from . ttodo get 1
```

목록은 기본적으로 최신 등록 항목부터 표시합니다. 다음 조건을 함께 지정해 목록을 좁힐 수 있습니다.

| 옵션 | 사용 예 | 동작 |
|---|---|---|
| `--status` | `--status IN_PROGRESS` | 상태가 같은 항목 |
| `--assignee` | `--assignee "민지"` | 담당자 이름이 같은 항목 |
| `--priority` | `--priority HIGH` | 우선순위가 같은 항목 |
| `--due-date-from` | `--due-date-from 2026-10-01` | 해당 날짜 이후가 마감일인 항목(시작일 포함) |
| `--due-date-to` | `--due-date-to 2026-10-31` | 해당 날짜 이전이 마감일인 항목(종료일 포함) |
| `--tag` | `--tag 기획` | 해당 태그가 있는 항목 |
| `--limit` | `--limit 20` | 한 번에 표시할 항목 수(1~100, 기본 50) |
| `--offset` | `--offset 20` | 앞에서 건너뛸 항목 수(기본 0) |

여러 조건을 함께 쓰면 모든 조건을 만족하는 항목을 표시합니다.

```sh
uvx --from . ttodo list --status TODO --assignee "민지" --due-date-from 2026-10-01 --due-date-to 2026-10-31 --limit 20
```

## 할 일 수정하기

`update` 뒤에 ID와 바꿀 필드만 지정합니다. 생략한 필드는 기존 값 그대로 유지됩니다.

```sh
uvx --from . ttodo update 1 --status IN_PROGRESS --priority HIGH
uvx --from . ttodo update 1 --assignee "지수" --tag 검토 --tag 출시
```

태그를 지정하면 기존 태그 전체가 새 목록으로 바뀝니다. `description`, `assignee`, `due-date` 값을 지울 때는 각각 `--clear-description`, `--clear-assignee`, `--clear-due-date`를 사용합니다. 태그를 모두 지우려면 `--clear-tags`를 사용합니다.

```sh
uvx --from . ttodo update 1 --clear-due-date --clear-tags
```

## 할 일 삭제하기

```sh
uvx --from . ttodo delete 1
```

삭제는 확인을 묻지 않고 영구적으로 처리됩니다. 연결된 태그는 Todo에서 분리되며, 태그 이름은 다른 할 일에서 다시 사용할 수 있도록 보존됩니다.

## 서버 주소와 출력 형식

기본 API 서버 주소는 `http://127.0.0.1:8000`입니다. 이번 명령에만 다른 주소를 쓰려면 전역 옵션 `--base-url`을 명령 이름 앞에 둡니다.

```sh
uvx --from . ttodo --base-url http://localhost:9000 list
```

매번 같은 주소를 쓰려면 환경 변수 `TEAM_TODO_BASE_URL`을 설정합니다.

PowerShell:

```powershell
$env:TEAM_TODO_BASE_URL = "http://localhost:9000"
uvx --from . ttodo list
```

POSIX 셸:

```sh
TEAM_TODO_BASE_URL=http://localhost:9000 uvx --from . ttodo list
```

기본 출력은 사람이 읽기 쉬운 텍스트입니다. 결과를 다른 도구에서 사용하려면 명령 앞에 `--json`을 지정합니다.

```sh
uvx --from . ttodo --json list --limit 2
uvx --from . ttodo --json get 1
```

JSON 모드에서는 결과 데이터만 표준 출력으로 보냅니다. 삭제 성공은 응답 데이터가 없어 표준 출력이 비어 있습니다. 오류가 나면 오류 설명을 표시하고 종료 코드 `1`을 반환합니다. 명령 입력이 잘못되면 종료 코드 `2`를 반환합니다.

## 도움말

각 명령의 옵션과 예시는 `--help`로 확인할 수 있습니다.

```sh
uvx --from . ttodo --help
uvx --from . ttodo create --help
uvx --from . ttodo list --help
uvx --from . ttodo update --help
```

CLI 명령의 제품 요구사항과 상세 설계는 [CLI 제품 요구사항](PRD_CLI.md), [CLI 기술 설계](TSD_CLI.md), [CLI 테스트 시나리오](TEST_CASE_CLI.md)를 참고하세요.
