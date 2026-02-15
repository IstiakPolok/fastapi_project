# FastAPI Authentication & AI Chat Backend

A comprehensive FastAPI backend with authentication and AI chat features.

## Features

### Authentication System
- ✅ User registration (signup) with name, email, password, and confirm password
- ✅ User login with JWT token authentication
- ✅ Forgot password with email OTP
- ✅ Verify OTP
- ✅ Reset password with OTP
- ✅ Change password (requires current password, no OTP)

### AI Chat System
- ✅ Chat with AI assistant (OpenAI GPT)
- ✅ Conversation context management
- ✅ Chat history storage
- ✅ Get chat history with pagination
- ✅ Clear chat history

### User Management
- ✅ Get user profile
- ✅ Update user profile

## Project Structure

```
fastapi_project/
├── app/
│   ├── core/
│   │   ├── dependencies.py    # Dependency injection
│   │   └── security.py        # Security utilities
│   ├── models/
│   │   ├── user.py           # User model
│   │   ├── otp.py            # OTP model
│   │   └── chat.py           # Chat model
│   ├── routes/
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── chat.py           # Chat endpoints
│   │   └── user.py           # User endpoints
│   ├── schemas/
│   │   ├── user.py           # User schemas
│   │   ├── auth.py           # Auth schemas
│   │   └── chat.py           # Chat schemas
│   ├── services/
│   │   ├── email_service.py  # Email & OTP service
│   │   └── ai_service.py     # AI chat service
│   ├── config.py             # Configuration
│   ├── database.py           # Database setup
│   └── main.py               # FastAPI app
├── requirements.txt
└── .env.example
```

## Setup Instructions

### 1. Clone or Navigate to Project Directory
```bash
cd C:\Users\Tanjim\.gemini\antigravity\scratch\fastapi_project
```

### 2. Create Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
- `SECRET_KEY`: Generate a random secret key
- `OPENAI_API_KEY`: Your OpenAI API key
- `SMTP_USER`: Your email address
- `SMTP_PASSWORD`: Your email app password

**For Gmail:**
1. Enable 2-factor authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords

### 5. Run the Application
```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

#### POST `/api/auth/signup`
Register a new user
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "confirm_password": "password123"
}
```

#### POST `/api/auth/login`
Login user
```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

#### POST `/api/auth/forgot-password`
Request OTP for password reset
```json
{
  "email": "john@example.com"
}
```

#### POST `/api/auth/verify-otp`
Verify OTP code
```json
{
  "email": "john@example.com",
  "otp_code": "123456"
}
```

#### POST `/api/auth/reset-password`
Reset password with OTP
```json
{
  "email": "john@example.com",
  "otp_code": "123456",
  "new_password": "newpassword123",
  "confirm_password": "newpassword123"
}
```

#### POST `/api/auth/change-password`
Change password (requires authentication)
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword123",
  "confirm_password": "newpassword123"
}
```

### Chat (Requires Authentication)

#### POST `/api/chat`
Send message to AI
```json
{
  "message": "Hello! How are you?"
}
```

#### GET `/api/chat/history?limit=50&offset=0`
Get chat history with pagination

#### DELETE `/api/chat/history`
Clear all chat history

### User (Requires Authentication)

#### GET `/api/user/me`
Get current user profile

#### PUT `/api/user/me`
Update user profile
```json
{
  "name": "John Updated",
  "email": "newemail@example.com"
}
```

## Authentication

For protected endpoints, include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Database

By default, the project uses SQLite (`app.db`). For production, configure PostgreSQL in the `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## Technologies Used

- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **JWT** - Authentication
- **Bcrypt** - Password hashing
- **OpenAI** - AI chat
- **SMTP** - Email sending

## License

MIT
