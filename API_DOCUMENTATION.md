# Senior Companion — API Documentation (Milestone 3)

> **Base URL:** `http://<host>:8001`
> **Auth:** All endpoints require a `Bearer` token in the `Authorization` header.
> **Swagger UI:** `{BASE_URL}/docs`

---

## 🔐 Authentication (unchanged)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/signup` | None | Register a new user |
| POST | `/api/auth/login` | None | Login and get JWT token |

### POST `/api/auth/signup`

```json
// Request
{
  "name": "Martha",
  "email": "martha@example.com",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123"
}

// Response 201
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### POST `/api/auth/login`

```json
// Request
{
  "email": "martha@example.com",
  "password": "SecurePass123"
}

// Response 200
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

---

## 💬 Chat — User Endpoints

> **Architecture:** Single-thread only. One continuous conversation per user. No sessions, no "new chat."

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/chat` | User | Send a message, get AI response |
| GET | `/api/chat/history` | User | Get unified conversation timeline |
| DELETE | `/api/chat/history` | User | Soft-delete all chat history |

---

### POST `/api/chat`

Send a message to the AI companion. The AI uses the user's name, long-term RAG memory (ChromaDB), and the last 10 messages as context.

**Headers:**
```
Authorization: Bearer <user_token>
```

**Request Body:**
```json
{
  "message": "Good morning! How are you today?"
}
```

**Response `200`:**
```json
{
  "id": 42,
  "message": "Good morning! How are you today?",
  "response": "Good morning, Martha! I'm so happy to hear from you today! How did you sleep last night?",
  "created_at": "2026-02-16T10:30:00Z"
}
```

**Errors:**
| Code | Detail |
|------|--------|
| 401 | Invalid or missing token |
| 500 | AI service error |

---

### GET `/api/chat/history`

Returns the unified conversation timeline. Soft-deleted messages are **never** returned.

**Headers:**
```
Authorization: Bearer <user_token>
```

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | Max messages to return |
| `offset` | int | 0 | Pagination offset |

**Response `200`:**
```json
{
  "chats": [
    {
      "id": 42,
      "message": "Good morning!",
      "response": "Good morning, Martha!...",
      "created_at": "2026-02-16T10:30:00Z"
    },
    {
      "id": 41,
      "message": "Tell me a story",
      "response": "Of course, Martha! ...",
      "created_at": "2026-02-16T09:15:00Z"
    }
  ],
  "total": 2
}
```

> **Note:** Results are ordered by `created_at DESC` (newest first).

---

### DELETE `/api/chat/history`

Soft-deletes all of the user's chat messages. Records remain in the database with `is_deleted = true` but are hidden from the user and the AI.

**Headers:**
```
Authorization: Bearer <user_token>
```

**Response `200`:**
```json
{
  "message": "Soft-deleted 15 chat messages"
}
```

---

## 🛡️ Admin — Companion Endpoints

> **Auth:** All admin endpoints require an **admin** JWT token (obtained via `/api/admin/auth/login`).

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/admin/summary/{user_id}` | Admin | AI emotional-status summary |
| GET | `/api/admin/chat/{user_id}` | Admin | View all chats (active + deleted) |
| DELETE | `/api/admin/chat/{user_id}` | Admin | Soft-delete or permanently delete |

---

### GET `/api/admin/summary/{user_id}`

Returns a **3-sentence AI-generated emotional-status summary** of the user. The admin never sees raw chat logs — only the synthesised analysis.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Path Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `user_id` | int | Target user's ID |

**Response `200`:**
```json
{
  "user_id": 5,
  "user_name": "Martha",
  "emotional_summary": "Martha appears to be in generally positive spirits, frequently sharing stories about her granddaughter Lily. She has expressed some feelings of loneliness in the evenings, particularly on weekends. Overall, she seems engaged and responsive, with a healthy interest in daily activities and family connections.",
  "message_count": 47,
  "generated_at": "2026-02-16T10:52:00Z"
}
```

**Errors:**
| Code | Detail |
|------|--------|
| 401 | Invalid or missing admin token |
| 403 | Non-admin token used |
| 404 | User not found |
| 500 | Summary generation failed |

---

### GET `/api/admin/chat/{user_id}`

View a user's **full chat history** including both active and soft-deleted messages. Each message shows its `is_deleted` status.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Path Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `user_id` | int | Target user's ID |

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 100 | Max messages (1–500) |
| `offset` | int | 0 | Pagination offset |
| `filter` | string | *(none)* | `"active"`, `"deleted"`, or omit for all |

**Response `200`:**
```json
{
  "user_name": "Martha",
  "chats": [
    {
      "id": 42,
      "user_id": 5,
      "message": "Good morning!",
      "response": "Good morning, Martha!...",
      "is_deleted": false,
      "created_at": "2026-02-16T10:30:00Z"
    },
    {
      "id": 38,
      "user_id": 5,
      "message": "I feel lonely today",
      "response": "I'm so sorry to hear that, Martha...",
      "is_deleted": true,
      "created_at": "2026-02-15T18:00:00Z"
    }
  ],
  "total": 50,
  "active_count": 47,
  "deleted_count": 3
}
```

**Filter examples:**
```
GET /api/admin/chat/5                    → all chats
GET /api/admin/chat/5?filter=active      → only active chats
GET /api/admin/chat/5?filter=deleted     → only soft-deleted chats
GET /api/admin/chat/5?limit=20&offset=20 → paginated
```

---

### DELETE `/api/admin/chat/{user_id}`

Delete a user's chat history. Supports both **soft-delete** and **permanent delete**.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Path Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `user_id` | int | Target user's ID |

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `permanent` | bool | `false` | `true` = hard delete from DB; `false` = soft-delete |

#### Soft-Delete (default)

```
DELETE /api/admin/chat/5
```

```json
// Response 200
{
  "message": "Soft-deleted 15 chat messages for user Martha",
  "user_id": 5,
  "deleted_count": 15,
  "permanent": false
}
```

Sets `is_deleted = true` on all active chats. AI will no longer access them, but admin can still view them via `GET /api/admin/chat/{user_id}?filter=deleted`.

#### Permanent Delete

```
DELETE /api/admin/chat/5?permanent=true
```

```json
// Response 200
{
  "message": "Permanently deleted 18 chat messages for user Martha",
  "user_id": 5,
  "deleted_count": 18,
  "permanent": true
}
```

Removes **ALL** chats (active + previously soft-deleted) from both PostgreSQL and ChromaDB. **This action is irreversible.**

**Errors:**
| Code | Detail |
|------|--------|
| 401 | Invalid or missing admin token |
| 403 | Non-admin token used |
| 404 | User not found |

---

## 📐 Data Models Reference

### ChatResponse (User-facing)

```typescript
{
  id:         number;     // unique message ID
  message:    string;     // user's message
  response:   string;     // AI's response
  created_at: string;     // ISO 8601 timestamp
}
```

### AdminChatResponse (Admin-facing)

```typescript
{
  id:         number;
  user_id:    number;
  message:    string;
  response:   string;
  is_deleted: boolean;    // true = soft-deleted
  created_at: string;
}
```

### AdminSummaryResponse

```typescript
{
  user_id:           number;
  user_name:         string;
  emotional_summary: string;   // 3-sentence AI analysis
  message_count:     number;   // active (non-deleted) messages
  generated_at:      string;
}
```

---

## ⚙️ Architecture Notes (for developers)

| Concept | Detail |
|---------|--------|
| **Single-thread** | One continuous conversation per user — no sessions |
| **Sliding window** | Last 10 non-deleted messages sent to OpenAI for context |
| **RAG memory** | ChromaDB stores embeddings of every exchange for long-term recall |
| **Soft-delete** | `is_deleted = true` hides from user + AI; admin can still see |
| **Permanent delete** | Removes rows from PostgreSQL + embeddings from ChromaDB |
| **Moderation** | Every AI response is scanned via keyword filter; flagged exchanges logged to `moderation_logs` table |
| **Identity layer** | AI always uses the user's registered name in responses |
