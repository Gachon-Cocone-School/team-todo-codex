# Team Todo

Team Todo는 로컬 팀에서 할 일을 함께 관리하는 API와 터미널 도구입니다. Python 3.11과 `uv`로 실행하며, 데이터는 기본적으로 프로젝트의 `data/team_todo.db`에 저장합니다.

## 시작하기

### 준비

- Python 3.11
- [uv](https://docs.astral.sh/uv/)

저장소 루트에서 의존성을 설치하고 데이터베이스를 준비합니다.

```sh
uv sync --all-groups
uv run alembic upgrade head
```

### API 서버 실행

```sh
uv run uvicorn app.main:app --reload --host 127.0.0.1
```

서버를 실행한 터미널을 열어 둡니다. Swagger UI는 <http://127.0.0.1:8000/docs>에서 사용할 수 있습니다. 대화형 API 문서에서 `POST /api/v1/todos`로 할 일을 만들고, 목록·상세·수정·삭제 요청을 실행할 수 있습니다.

서버는 기본적으로 이 컴퓨터에서만 접근할 수 있는 `127.0.0.1`에 바인딩합니다. 인증 기능이 없으므로 신뢰할 수 없는 네트워크에 공개하지 마세요.

### 터미널에서 할 일 관리

CLI의 설치, 명령 옵션, 필터, 출력 형식은 [CLI 사용 설명서](docs/CLI_GUIDE.md)를 참고하세요.

서버가 실행 중인 상태에서 새 터미널을 열고 저장소 루트에서 명령을 실행합니다.

```sh
uvx --from . ttodo --help
uvx --from . ttodo create --title "회의 자료 준비" --assignee "민지" --due-date 2026-10-15 --priority HIGH --tag 기획 --tag 회의
uvx --from . ttodo list --status TODO
uvx --from . ttodo get 1
uvx --from . ttodo update 1 --status DONE
uvx --from . ttodo delete 1
```

`uvx`는 CLI 실행 환경을 준비합니다. 개발 환경을 이미 동기화했다면 `uv run ttodo --help`처럼 실행할 수 있습니다. `delete`는 확인을 묻지 않고 영구 삭제하므로 ID를 확인한 뒤 사용하세요.

목록에서 상태, 담당자, 우선순위, 마감일, 태그로 검색할 수 있습니다. 한 번에 최대 100개를 표시하며 기본값은 50개입니다.

```sh
uvx --from . ttodo list --assignee "민지" --due-date-from 2026-10-01 --due-date-to 2026-10-31 --limit 20
```

수정 명령은 지정한 항목만 바꿉니다. 설명, 담당자, 마감일을 지우려면 해당 `--clear-*` 옵션을 사용하고, 태그를 바꾸려면 `--tag`를 지정합니다. `--clear-tags`는 태그를 모두 제거합니다.

```sh
uvx --from . ttodo update 1 --assignee "지수" --tag 검토 --tag 출시
uvx --from . ttodo update 1 --clear-due-date
```

기본 서버 주소는 `http://127.0.0.1:8000`입니다. 다른 서버를 쓰려면 `--base-url`을 지정하거나 `TEAM_TODO_BASE_URL` 환경 변수를 설정합니다. `--json`은 결과를 JSON으로 출력하며, 전역 옵션이므로 명령 이름 앞에 둡니다.

```sh
uvx --from . ttodo --base-url http://localhost:9000 --json list
```

PowerShell:

```powershell
$env:TEAM_TODO_BASE_URL = "http://localhost:9000"
uvx --from . ttodo list
```

POSIX 셸:

```sh
TEAM_TODO_BASE_URL=http://localhost:9000 uvx --from . ttodo list
```

## 데이터베이스 설정과 초기화

기본 SQLite 데이터베이스 위치를 바꾸려면 `DATABASE_URL`을 지정한 뒤 마이그레이션을 실행하고 서버를 시작합니다.

```sh
DATABASE_URL=sqlite:///./data/local.db uv run alembic upgrade head
DATABASE_URL=sqlite:///./data/local.db uv run uvicorn app.main:app --reload --host 127.0.0.1
```

PowerShell에서는 `$env:DATABASE_URL = "sqlite:///./data/local.db"`로 설정합니다. 데이터베이스를 완전히 비우려면 서버를 중지하고 해당 SQLite DB 파일과 같은 이름의 `-wal`, `-shm` 파일이 있으면 함께 삭제한 뒤 `uv run alembic upgrade head`를 실행합니다. 이 작업은 저장된 할 일을 영구적으로 지웁니다.

## 개발과 검증

```sh
uv run pytest
./scripts/check.sh
```

`./scripts/check.sh`는 Ruff 검사, 포맷 확인, 전체 테스트를 실행합니다. 기여 전 Git hook을 설치하려면 `./scripts/install-git-hooks.sh`를 실행합니다.

## 문서

- [CLI 사용 설명서](docs/CLI_GUIDE.md)
- [제품 요구사항](docs/PRD.md) 및 [CLI 요구사항](docs/PRD_CLI.md)
- [API 기술 설계](docs/TSD.md) 및 [CLI 기술 설계](docs/TSD_CLI.md)
- [데이터베이스 설계](docs/DATABASE.md)
- [API 테스트 시나리오](docs/TEST_CASE.md) 및 [CLI 테스트 시나리오](docs/TEST_CASE_CLI.md)
- [보안 감사](docs/SECURITY_AUDIT.md) 및 [성능 감사](docs/PERFORMANCE_AUDIT.md)
