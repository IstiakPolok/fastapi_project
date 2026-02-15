# Quick Start Guide

## ✅ Installation Complete!

Your FastAPI backend is now successfully installed and running!

### Server Status
- ✅ Dependencies installed
- ✅ Environment configured
- ✅ Server running on: **http://localhost:8000**

---

## 📖 Access API Documentation

Open your web browser and navigate to:

### Swagger UI (Interactive API Docs)
**http://localhost:8000/docs**

This provides an interactive interface where you can:
- View all available endpoints
- Test each endpoint directly in the browser
- See request/response schemas
- Authenticate and test protected endpoints

### ReDoc (Alternative Documentation)
**http://localhost:8000/redoc**

---

## 🧪 Quick Test Guide

### 1. Test User Registration

1. Open http://localhost:8000/docs
2. Find `POST /api/auth/signup`
3. Click "Try it out"
4. Use this example:
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "password123",
  "confirm_password": "password123"
}
```
5. Click "Execute"
6. Copy the `access_token` from the response

### 2. Authenticate

1. Click the "Authorize" button at the top of the page
2. Enter: `Bearer YOUR_ACCESS_TOKEN`
3. Click "Authorize"

### 3. Test AI Chat

1. Find `POST /api/chat`
2. Click "Try it out"
3. Enter:
```json
{
  "message": "Hello! How are you today?"
}
```
4. Click "Execute"
5. You should see the AI's friendly response!

---

## 📧 Email OTP Testing

> **Important**: For OTP emails to work, you need a Gmail App Password.

### Get Gmail App Password:

1. Go to your Google Account: https://myaccount.google.com
2. Select **Security**
3. Under "Signing in to Google," select **2-Step Verification** (enable if not already)
4. At the bottom of the page, select **App Passwords**
5. Select **Mail** and **Windows Computer**
6. Click **Generate**
7. Copy the 16-character password
8. Update your `.env` file with this password in `SMTP_PASSWORD`

### Test Forgot Password Flow:

1. Open http://localhost:8000/docs
2. Use `POST /api/auth/forgot-password` with your email
3. Check your inbox for the OTP
4. Use `POST /api/auth/verify-otp` to verify
5. Use `POST /api/auth/reset-password` to set a new password

---

## 🎯 All Available Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/forgot-password` - Request OTP via email
- `POST /api/auth/verify-otp` - Verify OTP code
- `POST /api/auth/reset-password` - Reset password with OTP
- `POST /api/auth/change-password` - Change password (requires current password)

### Chat (Protected - requires authentication)
- `POST /api/chat` - Send message to AI
- `GET /api/chat/history` - Get chat history
- `DELETE /api/chat/history` - Clear chat history

### User Profile (Protected - requires authentication)
- `GET /api/user/me` - Get your profile
- `PUT /api/user/me` - Update your profile

---

## 🛠️ Server Commands

### Start Server
```bash
uvicorn app.main:app --reload
```

### Stop Server
Press `Ctrl + C` in the terminal

### View Server Logs
The terminal window shows all requests and responses in real-time

---

## ⚠️ Important Notes

> **Gmail SMTP**: The password in `.env` should be a Gmail App Password, not your regular Gmail password.

> **OpenAI API**: Make sure your OpenAI API key is valid and has available credits.

> **Secret Key**: For production, generate a strong secret key using:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## 🔍 Troubleshooting

### OTP emails not sending?
- Verify Gmail App Password is correct
- Check that 2-Step Verification is enabled on your Google account
- Ensure `FROM_EMAIL` matches `SMTP_USER` in `.env`

### AI not responding?
- Check OpenAI API key is valid
- Verify you have API credits available
- Check server logs for error messages

### Database errors?
- The database file `app.db` is created automatically
- Delete `app.db` to reset the database

---

## 📝 Next Steps

1. ✅ Open http://localhost:8000/docs in your browser
2. ✅ Test the signup endpoint
3. ✅ Authenticate using the token
4. ✅ Test the AI chat feature
5. ✅ Explore all endpoints

**Your backend is ready for frontend integration!**
