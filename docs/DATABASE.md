# 팀 Todo 데이터베이스 설계

## 1. 개요

SQLite를 로컬 영속 저장소로 사용한다. SQLAlchemy 2.x로 접근하고 Alembic으로 스키마 변경을 관리한다. 기본 DB URL은 `sqlite:///./data/team_todo.db`이며, DB 파일은 저장소에 커밋하지 않는다.

## 2. 관계

```text
todos 1 ─── * todo_tags * ─── 1 tags
```

`todo_tags`는 할 일과 태그의 다대다 연결을 표현한다. 같은 태그 이름은 여러 할 일에서 재사용한다.

## 3. 테이블

### `todos`

| 컬럼 | 타입 | NULL | 제약/설명 |
|---|---|---:|---|
| `id` | INTEGER | 아니오 | 기본 키, 자동 증가 |
| `title` | VARCHAR(200) | 아니오 | trim 후 1~200자 |
| `description` | TEXT | 예 | 최대 5000자 |
| `assignee` | VARCHAR(100) | 예 | 자유 입력 이름 |
| `due_date` | DATE | 예 | 마감일, 시간대 없음 |
| `priority` | VARCHAR(10) | 아니오 | `LOW`, `MEDIUM`, `HIGH`; 기본 `MEDIUM` |
| `status` | VARCHAR(20) | 아니오 | `TODO`, `IN_PROGRESS`, `DONE`; 기본 `TODO` |
| `created_at` | DATETIME | 아니오 | UTC, 생성 시 설정 |
| `updated_at` | DATETIME | 아니오 | UTC, 생성·수정 시 설정 |

`priority`, `status`에는 CHECK 제약을 둬 허용 enum 밖의 값이 저장되지 않게 한다.

### `tags`

| 컬럼 | 타입 | NULL | 제약/설명 |
|---|---|---:|---|
| `id` | INTEGER | 아니오 | 기본 키, 자동 증가 |
| `name` | VARCHAR(50) | 아니오 | trim 후 비어 있지 않은 태그 이름 |

태그 이름에는 대소문자를 구분하지 않는 고유 인덱스를 둔다. SQLite에서는 `name COLLATE NOCASE` 고유 인덱스를 사용한다. 저장 시 trim을 적용하고, 출력 시 최초 생성 시의 표기를 유지한다.

### `todo_tags`

| 컬럼 | 타입 | NULL | 제약/설명 |
|---|---|---:|---|
| `todo_id` | INTEGER | 아니오 | `todos.id` 외래 키, 삭제 시 CASCADE |
| `tag_id` | INTEGER | 아니오 | `tags.id` 외래 키, 삭제 시 CASCADE |

복합 기본 키는 `(todo_id, tag_id)`로 두어 동일 연결의 중복을 막는다. 태그 레코드가 더 이상 연결되지 않아도 보존하여 이후 재사용할 수 있다.

## 4. 인덱스

- `todos(status, created_at)` — 상태 필터와 기본 정렬 보조
- `todos(assignee)` — 담당자 필터
- `todos(priority)` — 우선순위 필터
- `todos(due_date)` — 마감일 필터
- `tags(name COLLATE NOCASE)` — 태그 이름 조회 및 중복 방지 (고유)
- `todo_tags(tag_id, todo_id)` — 태그별 할 일 목록 조회

기본 정렬의 동률 결정에 쓰이는 `id`는 기본 키 인덱스를 사용한다.

## 5. 무결성 및 삭제 규칙

- 할 일 제목, 상태, 우선순위, 생성·수정 시각은 필수다.
- 날짜는 ISO 날짜(`YYYY-MM-DD`) 형태로 읽고 쓴다.
- `todos` 삭제 시 연결 테이블 행은 외래 키 CASCADE로 삭제한다.
- SQLite 외래 키 검사는 연결마다 활성화한다 (`PRAGMA foreign_keys=ON`).
- 파일 기반 SQLite 연결은 WAL, `busy_timeout`을 사용해 읽기/쓰기 경합 시 대기하도록 한다. 기본 대기 시간은 30초이며 `SQLITE_BUSY_TIMEOUT_MS`로 조정한다.
- 풀 한도는 `DATABASE_POOL_SIZE`(기본 10), `DATABASE_MAX_OVERFLOW`(기본 20), `DATABASE_POOL_TIMEOUT`(기본 30초)으로 설정할 수 있다. SQLite는 단일 writer이므로 풀 크기 확대가 쓰기 처리량을 선형으로 늘리지는 않는다.
- HTTP 요청의 동시 DB 진입 수는 풀 최대 크기(`size + overflow`)로 제한한다. SQLite 쓰기는 앱 프로세스 안에서 직렬 처리해 동시 writer 경합이 커넥션 풀 고갈로 번지지 않게 한다.
- 태그가 고아 상태가 되어도 자동 삭제하지 않는다. 태그 재사용과 데이터 처리 단순성을 우선한다.
- 삭제는 논리 삭제가 아닌 영구 삭제다.

## 6. 시간 처리

`due_date`는 날짜만 저장하므로 UTC 변환을 적용하지 않는다. `created_at`과 `updated_at`은 UTC 기준으로 기록하고 API에서는 `Z`가 포함된 ISO 8601 문자열로 반환한다. SQLite의 datetime 컬럼은 시간대 정보를 보존하지 않으므로 ORM 변환 경계에서 UTC 기준을 명시적으로 적용한다.

## 7. 마이그레이션 및 백업

- Alembic 초기 마이그레이션이 위 테이블, 제약, 인덱스를 생성한다.
- DB 스키마 변경은 새 마이그레이션으로 추가하며, 기존 데이터를 보존하는 방향으로 작성한다.
- 로컬 백업은 앱을 정지한 뒤 SQLite 파일을 복사한다. WAL 모드를 사용한다면 SQLite의 일관된 백업 절차를 사용한다.
- 테스트는 임시 DB 파일 또는 격리된 메모리 DB를 사용한다.
