# 팀 Todo 백엔드 기술 설계 (TSD)

## 1. 기술 스택

- Python 3.11
- FastAPI 및 Uvicorn
- Pydantic v2 설정·요청 검증
- SQLAlchemy 2.x ORM
- SQLite
- Alembic 스키마 마이그레이션
- pytest 및 FastAPI TestClient 기반 API 검증

의존성 버전은 구현 시 호환되는 안정 버전으로 고정한다.

## 2. Python 개발 환경

- Python 버전은 3.11로 고정한다. `.python-version`에 `3.11`을 기록하고 `pyproject.toml`은 `>=3.11,<3.12`를 요구한다.
- 패키지와 가상환경은 `uv`로 관리한다. `uv.lock`은 재현성을 위해 저장소에 포함한다.
- 최초 설치 및 동기화: `uv sync --all-groups`
- 개발 서버: `uv run uvicorn app.main:app --reload`
- 마이그레이션: `uv run alembic upgrade head`
- 테스트 실행: `uv run pytest`
- 전체 품질 게이트: `./scripts/check.sh` (Ruff lint, 포맷 확인, pytest)
- 안전한 lint/포맷 자동 수정: `./scripts/fix.sh`
- Git pre-commit hook은 전체 품질 게이트를 실행한다. clone 후 `./scripts/install-git-hooks.sh`로 켠다.
- 런타임 의존성 추가/제거는 `uv add <package>` / `uv remove <package>`, 개발 의존성은 `uv add --dev <package>` / `uv remove --dev <package>`를 사용한다.
- `.venv`는 저장소에 포함하지 않는다.

## 3. 구성

```text
클라이언트 / Swagger UI
          |
       FastAPI
          |
  라우터 -> 서비스/검증
          |
 SQLAlchemy 세션
          |
       SQLite
```

권장 소스 구조:

```text
app/
  main.py              # FastAPI 앱, 라우터 및 예외 처리 연결
  core/config.py       # 환경 설정
  db/session.py        # 엔진과 요청 단위 세션
  models/              # SQLAlchemy 모델
  schemas/             # Pydantic 요청·응답 모델
  api/routes/todos.py  # Todo HTTP 엔드포인트
  services/todos.py    # 목록 필터와 쓰기 규칙
alembic/               # DB 마이그레이션
tests/                 # API 및 서비스 검증
data/                  # 기본 SQLite 파일 위치(버전 관리 제외)
```

## 4. 실행 및 설정

- 로컬 실행 기본 주소는 `http://127.0.0.1:8000`이다.
- 설정은 환경 변수로 덮어쓸 수 있게 한다. 최소 설정값은 `DATABASE_URL`이며 기본값은 `sqlite:///./data/team_todo.db`이다.
- SQLite 파일을 열기 전에 상위 디렉터리를 생성한다.
- SQLite 엔진에 `check_same_thread=False`를 적용하고, 요청 단위로 세션을 열고 닫는다.
- SQLite 파일 DB는 WAL과 busy timeout(기본 30초)을 사용한다. SQLAlchemy 풀은 `DATABASE_POOL_SIZE`(10), `DATABASE_MAX_OVERFLOW`(20), `DATABASE_POOL_TIMEOUT`(30초) 설정을 지원한다. 요청 동시 실행은 풀 최대 크기(`size + overflow`)로 제한해 초과 요청이 DB 세션과 스레드를 점유하지 않고 대기한다. SQLite 쓰기는 프로세스 내에서 직렬화되므로 큰 쓰기 처리량이나 다중 프로세스 운영이 필요하면 PostgreSQL을 사용한다.
- 개발 실행 명령 예: `uv run uvicorn app.main:app --reload`.
- `/docs`, `/redoc`, `/openapi.json`은 FastAPI 기본 문서 경로를 사용한다.

## 5. API 설계

기본 경로는 `/api/v1/todos`이다. JSON 요청·응답을 사용한다.

| 메서드 | 경로 | 동작 | 성공 응답 |
|---|---|---|---|
| `POST` | `/api/v1/todos` | Todo 생성 | `201`, 생성된 Todo |
| `GET` | `/api/v1/todos` | 목록 및 필터 조회 | `200`, 페이지 결과 |
| `GET` | `/api/v1/todos/{todo_id}` | 단건 조회 | `200`, Todo |
| `PATCH` | `/api/v1/todos/{todo_id}` | 전달 필드 부분 수정 | `200`, 수정된 Todo |
| `DELETE` | `/api/v1/todos/{todo_id}` | 영구 삭제 | `204`, 본문 없음 |

### Todo 표현

```json
{
  "id": 1,
  "title": "회의 자료 준비",
  "description": null,
  "assignee": "민지",
  "due_date": "2026-10-15",
  "priority": "HIGH",
  "status": "IN_PROGRESS",
  "tags": ["기획", "회의"],
  "created_at": "2026-10-07T04:00:00Z",
  "updated_at": "2026-10-07T04:00:00Z"
}
```

### 목록 질의 매개변수

- `status`: 상태 enum
- `assignee`: 담당자 이름 완전 일치
- `priority`: 우선순위 enum
- `due_date_from`, `due_date_to`: 포함 범위 날짜 (`YYYY-MM-DD`)
- `tag`: 태그 이름 완전 일치, 대소문자 구분 없이 필터
- `limit`: 1~100, 기본 50
- `offset`: 0 이상, 기본 0

목록 응답은 `{ "items": [...], "limit": 50, "offset": 0 }` 형태로 반환한다. 기본 정렬은 `created_at DESC, id DESC`이다.

### 입력 규칙과 오류

- 제목은 trim 후 1~200자다. 설명은 최대 5000자, 담당자는 최대 100자다.
- 태그는 문자열 배열이며 각 태그는 trim 후 1~50자다. 요청 안 중복 태그는 정규화 후 한 번만 저장한다.
- `PATCH`에서 필드를 생략하면 기존 값을 유지한다. nullable 필드(`description`, `assignee`, `due_date`)에 명시적으로 `null`을 보내면 값을 비운다. `tags`를 생략하면 유지하고 `[]`이면 모두 제거한다.
- `PATCH`에 변경 필드가 하나도 없으면 `422`를 반환한다. `due_date_from`이 `due_date_to`보다 늦으면 `422`를 반환한다.
- 유효하지 않은 필드 값은 `422`; 존재하지 않는 ID는 `404`; DB 제약 위반은 내부 오류 정보가 노출되지 않는 `409` 또는 검증 오류로 변환한다.
- 오류 본문은 FastAPI의 표준 `detail` 형식을 사용한다. 예상하지 못한 오류에는 내부 SQL이나 스택 트레이스를 노출하지 않는다.

## 6. 요청 처리 및 데이터 접근

- 라우터는 HTTP 입력·출력과 상태 코드를 담당한다.
- 서비스 계층은 태그 정규화, 필터 조합, 생성·수정·삭제 규칙을 담당한다.
- DB 세션은 FastAPI dependency로 주입하고 요청이 끝나면 닫는다.
- 각 쓰기 요청은 하나의 트랜잭션으로 처리한다. Todo와 태그 연결은 함께 성공하거나 함께 롤백한다.
- DB 레코드가 없으면 서비스에서 `404`로 처리한다.
- 목록 쿼리는 필터를 SQL에서 적용하고, 응답 크기 제한은 `limit` 상한으로 관리한다.

## 7. 동시성 및 안전한 실행

- 실시간 연결, WebSocket, 푸시 기능은 구현하지 않는다.
- SQLite의 단일 파일/단일 호스트 사용을 전제로 한다. 큰 동시 쓰기 부하나 다중 서버 운영은 목표 범위가 아니다.
- 인증이 없으므로 기본 바인딩은 loopback 주소(`127.0.0.1`)로 한다. LAN 공개가 필요하면 별도 인증·접근 통제를 먼저 설계한다.
- CORS는 필요한 로컬 프론트엔드 origin만 설정으로 허용하며, 기본값은 넓은 와일드카드로 열지 않는다.
- DB 파일은 저장소에 커밋하지 않으며 백업은 파일 복사 방식으로 가능하다.

## 8. 마이그레이션 및 실행 흐름

1. `uv sync --all-groups`로 가상환경과 의존성을 준비한다.
2. DB 경로 설정을 확인하고 `uv run alembic upgrade head`로 스키마를 준비한다.
3. `uv run uvicorn app.main:app --reload`로 로컬 서버를 실행한다.
4. `/docs`에서 API를 사용한다.

초기 구현에서 Alembic 마이그레이션을 제공한다. 앱 시작 시 임의로 테이블을 자동 변경하지 않는다.

## 9. 검증 계획

- 생성·목록·단건 조회·부분 수정·삭제의 상태 코드와 응답 스키마
- 잘못된 enum, 제목, 날짜, 태그 입력
- 각 목록 필터의 조합, 페이지네이션, 기본 정렬
- 태그의 중복 정규화와 재사용, Todo 삭제 시 연결 삭제
- SQLite 파일 재오픈 후 데이터 유지
- OpenAPI 문서에 경로와 enum이 노출되는지 확인

테스트는 임시 SQLite DB를 주입해 실행하고 개발 DB를 변경하지 않는다.
