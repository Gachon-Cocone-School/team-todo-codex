# 팀 Todo API 테스트 케이스

## 공통 기준

- 기본 URL: `http://127.0.0.1:8000`
- API prefix: `/api/v1`
- 모든 요청과 응답은 JSON이다. `DELETE` 성공 응답은 본문이 없다.
- 성공/실패 테스트는 서로 독립적으로 실행한다. ID 예시 `1`은 해당 케이스에서 준비한 리소스 ID를 뜻한다.
- 응답의 `created_at`, `updated_at`은 UTC ISO 8601 형식이며, 실제 값 비교가 필요한 경우 날짜 형식과 시각 갱신 여부를 확인한다.
- 오류 응답은 FastAPI `detail` 구조를 사용하며, 세부 메시지 문구보다 HTTP 상태 코드와 오류 위치·내용의 존재를 확인한다.

## 성공 케이스

### TC-S01 — 기본값으로 Todo 생성

- [ ] **Endpoint:** `POST /api/v1/todos`
- [ ] **Request:**

  ```json
  { "title": "회의 자료 준비" }
  ```

- [ ] **Expected response:** `201 Created`; 응답에 생성된 `id`, `title: "회의 자료 준비"`, `status: "TODO"`, `priority: "MEDIUM"`, 빈 `tags`, `created_at`, `updated_at`이 포함된다. 설명, 담당자, 마감일은 `null`이다.

### TC-S02 — 선택 필드와 여러 태그를 포함해 생성

- [ ] **Endpoint:** `POST /api/v1/todos`
- [ ] **Request:**

  ```json
  {
    "title": "출시 점검",
    "description": "배포 전 확인 목록 점검",
    "assignee": "민지",
    "due_date": "2026-10-15",
    "priority": "HIGH",
    "status": "IN_PROGRESS",
    "tags": ["출시", "검토"]
  }
  ```

- [ ] **Expected response:** `201 Created`; 입력한 필드와 두 태그가 정규화된 형태로 반환되고, 생성·수정 시각이 포함된다.

### TC-S03 — Todo 목록 조회 및 기본 정렬

- [ ] **Endpoint:** `GET /api/v1/todos`
- [ ] **Request:** query 없음
- [ ] **Expected response:** `200 OK`; `{ "items": [...], "limit": 50, "offset": 0 }` 형식이다. 생성 시각 내림차순, 동률이면 ID 내림차순으로 반환된다.

### TC-S04 — 상태로 필터링

- [ ] **Endpoint:** `GET /api/v1/todos?status=DONE`
- [ ] **Request:** query `status=DONE`
- [ ] **Expected response:** `200 OK`; 반환된 모든 `items`의 상태가 `DONE`이다. 결과가 없으면 `items`는 빈 배열이다.

### TC-S05 — 담당자와 우선순위로 필터링

- [ ] **Endpoint:** `GET /api/v1/todos?assignee=%EB%AF%BC%EC%A7%80&priority=HIGH`
- [ ] **Request:** 담당자 `민지`, 우선순위 `HIGH`
- [ ] **Expected response:** `200 OK`; 반환된 모든 항목의 담당자가 `민지`이고 우선순위가 `HIGH`이다.

### TC-S06 — 마감일 범위로 필터링

- [ ] **Endpoint:** `GET /api/v1/todos?due_date_from=2026-10-01&due_date_to=2026-10-31`
- [ ] **Request:** 양 끝 날짜를 포함하는 마감일 범위
- [ ] **Expected response:** `200 OK`; 모든 항목의 마감일이 `2026-10-01` 이상, `2026-10-31` 이하이다. 마감일이 없는 항목은 포함되지 않는다.

### TC-S07 — 태그로 필터링

- [ ] **Endpoint:** `GET /api/v1/todos?tag=%EC%B6%9C%EC%8B%9C`
- [ ] **Request:** 태그 `출시`
- [ ] **Expected response:** `200 OK`; 반환된 모든 항목이 대소문자 구분 없이 `출시` 태그를 하나 이상 가진다.

### TC-S08 — 페이지네이션

- [ ] **Endpoint:** `GET /api/v1/todos?limit=2&offset=1`
- [ ] **Request:** `limit=2`, `offset=1`
- [ ] **Expected response:** `200 OK`; `limit`은 2, `offset`은 1이고 `items`는 최대 2개다. 같은 데이터에 대해 반복 조회하면 정렬 순서가 안정적이다.

### TC-S09 — Todo 단건 조회

- [ ] **Endpoint:** `GET /api/v1/todos/1`
- [ ] **Request:** 경로 ID `1`
- [ ] **Expected response:** `200 OK`; ID가 1인 Todo 전체와 태그 배열, 생성·수정 시각이 반환된다.

### TC-S10 — 일부 필드 수정

- [ ] **Endpoint:** `PATCH /api/v1/todos/1`
- [ ] **Request:**

  ```json
  { "status": "DONE", "priority": "LOW" }
  ```

- [ ] **Expected response:** `200 OK`; 상태와 우선순위가 변경되고 전달하지 않은 제목·담당자·마감일·태그는 유지된다. `updated_at`은 이전 값보다 늦다.

### TC-S11 — nullable 필드 비우기 및 태그 전체 제거

- [ ] **Endpoint:** `PATCH /api/v1/todos/1`
- [ ] **Request:**

  ```json
  { "description": null, "assignee": null, "due_date": null, "tags": [] }
  ```

- [ ] **Expected response:** `200 OK`; 해당 nullable 필드는 `null`, 태그는 빈 배열이다.

### TC-S12 — 태그 공백 제거와 중복 정규화

- [ ] **Endpoint:** `POST /api/v1/todos`
- [ ] **Request:**

  ```json
  { "title": "태그 확인", "tags": [" 기획 ", "기획", "기획 "] }
  ```

- [ ] **Expected response:** `201 Created`; 응답 태그에는 공백이 제거된 `기획`이 한 번만 포함된다.

### TC-S13 — Todo 삭제

- [ ] **Endpoint:** `DELETE /api/v1/todos/1`
- [ ] **Request:** 경로 ID `1`
- [ ] **Expected response:** `204 No Content`; 응답 본문이 비어 있고 연결된 `todo_tags` 행도 제거된다.

## 실패 케이스

### TC-F01 — 제목 누락 또는 공백 제목으로 생성

- [ ] **Endpoint:** `POST /api/v1/todos`
- [ ] **Request:**

  ```json
  { "title": "   " }
  ```

- [ ] **Expected response:** `422 Unprocessable Entity`; `detail`에 `title` 입력 검증 오류가 포함되고 Todo가 생성되지 않는다. 제목 누락도 동일하게 422를 반환한다.

### TC-F02 — 제목 길이 초과

- [ ] **Endpoint:** `POST /api/v1/todos`
- [ ] **Request:** `title`이 201자 이상인 JSON
- [ ] **Expected response:** `422 Unprocessable Entity`; 제목 길이 오류가 반환되고 Todo가 생성되지 않는다.

### TC-F03 — 잘못된 상태 또는 우선순위

- [ ] **Endpoint:** `POST /api/v1/todos`
- [ ] **Request:**

  ```json
  { "title": "잘못된 enum", "status": "BLOCKED", "priority": "URGENT" }
  ```

- [ ] **Expected response:** `422 Unprocessable Entity`; `status`와 `priority` 검증 오류가 반환되고 Todo가 생성되지 않는다.

### TC-F04 — 잘못된 날짜 형식

- [ ] **Endpoint:** `POST /api/v1/todos`
- [ ] **Request:**

  ```json
  { "title": "날짜 검증", "due_date": "15-10-2026" }
  ```

- [ ] **Expected response:** `422 Unprocessable Entity`; `due_date` 형식 오류가 반환되고 Todo가 생성되지 않는다.

### TC-F05 — 빈 태그 또는 태그 길이 초과

- [ ] **Endpoint:** `POST /api/v1/todos`
- [ ] **Request:** 빈 문자열/공백 문자열 태그 또는 51자 이상 태그를 포함한 JSON
- [ ] **Expected response:** `422 Unprocessable Entity`; 태그 항목 오류가 반환되고 Todo 및 태그 연결이 생성되지 않는다.

### TC-F06 — 잘못된 필터 값

- [ ] **Endpoint:** `GET /api/v1/todos?status=BLOCKED`
- [ ] **Request:** 허용되지 않는 상태 필터
- [ ] **Expected response:** `422 Unprocessable Entity`; `status` query 검증 오류가 반환된다.

### TC-F07 — 잘못된 페이지네이션 값

- [ ] **Endpoint:** `GET /api/v1/todos?limit=101&offset=-1`
- [ ] **Request:** 최대값보다 큰 `limit`, 음수 `offset`
- [ ] **Expected response:** `422 Unprocessable Entity`; 잘못된 query 매개변수 오류가 반환된다.

### TC-F08 — 역전된 마감일 범위

- [ ] **Endpoint:** `GET /api/v1/todos?due_date_from=2026-10-31&due_date_to=2026-10-01`
- [ ] **Request:** 시작일이 종료일보다 늦은 범위
- [ ] **Expected response:** `422 Unprocessable Entity`; 날짜 범위 검증 오류가 반환된다.

### TC-F09 — 존재하지 않는 Todo 조회

- [ ] **Endpoint:** `GET /api/v1/todos/999999`
- [ ] **Request:** 존재하지 않는 ID
- [ ] **Expected response:** `404 Not Found`; `detail`에 Todo를 찾을 수 없다는 오류가 포함된다.

### TC-F10 — 존재하지 않는 Todo 수정

- [ ] **Endpoint:** `PATCH /api/v1/todos/999999`
- [ ] **Request:**

  ```json
  { "status": "DONE" }
  ```

- [ ] **Expected response:** `404 Not Found`; 기존 Todo나 태그 데이터가 변경되지 않는다.

### TC-F11 — 존재하지 않는 Todo 삭제

- [ ] **Endpoint:** `DELETE /api/v1/todos/999999`
- [ ] **Request:** 존재하지 않는 ID
- [ ] **Expected response:** `404 Not Found`; 삭제 대상이 없다는 오류가 반환된다.

### TC-F12 — 빈 수정 요청

- [ ] **Endpoint:** `PATCH /api/v1/todos/1`
- [ ] **Request:** `{}`
- [ ] **Expected response:** `422 Unprocessable Entity`; 수정할 필드가 없다는 검증 오류가 반환되고 Todo가 변경되지 않는다.

### TC-F13 — 잘못된 JSON 본문

- [ ] **Endpoint:** `POST /api/v1/todos`
- [ ] **Request:** JSON 문법이 잘못된 본문 (예: `{"title": "미완성}`)
- [ ] **Expected response:** `422 Unprocessable Entity`; 요청 본문 파싱 오류가 반환되고 Todo가 생성되지 않는다.
