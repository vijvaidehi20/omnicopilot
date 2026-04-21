# 🚀 OmniCopilot

**OmniCopilot** is a sophisticated AI assistant designed to act as a unified bridge between you and your digital workspace. By combining the power of Large Language Models (Gemini/OpenAI) with direct Google Workspace integrations, OmniCopilot allows you to manage your professional life through simple, natural conversations.

---

## ✨ Key Features

### 📅 Google Calendar
*   **Event Creation**: Automatically schedule meetings with Google Meet links included.
*   **Smart Updates**: Modify existing events (time, title, attendees) using natural language.
*   **Daily Briefings**: Ask the AI to summarize your upcoming schedule.

### 📧 Gmail Intelligence
*   **Inbox Access**: Fetch and summarize your 5 most recent emails.
*   **Instant Sending**: Send emails directly from the chat interface.
*   **Proactive Drafting**: Have the AI draft complex replies and save them to your Gmail drafts folder.

### 📂 Google Drive & Docs
*   **File Discovery**: List and search for your most recent Drive files.
*   **Doc Summarization**: Analyze and summarize the content of your latest Google Docs.
*   **Fast Creation**: Generate new Google Docs with formatted content directly from a prompt.

### ⏰ Productivity Tools
*   **Intelligent Reminders**: Set time-sensitive notifications that trigger real desktop/browser alerts.
*   **File Analysis**: Upload documents/images and ask the AI specific questions using OCR and advanced reasoning.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python, FastAPI, SQLAlchemy, SQLite/PostgreSQL |
| **AI Engine** | Groq (Inference) |
| **Integrations** | Google OAuth 2.0, Gmail API, Calendar API, Drive API |
| **Task Queue** | APScheduler (Reminders & Cleanup) |
| **Frontend** | React 19, Vite, Tailwind CSS 4, Axios |
| **UI Components** | Lucide React, React Markdown |

---

## 🚀 Getting Started

### 📋 Prerequisites
*   **Python 3.10+** and **Node.js 18+**
*   **Google Cloud Project**: Enabled APIs for Gmail, Calendar, Drive, and Google Docs.
*   **OAuth Credentials**: A `client_id` and `client_secret` from your Google Cloud Console.

### 🛠️ Backend Setup
1.  **Navigate and Install**:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
2.  **Environment Configuration**:
    Create a `.env` file in the `backend/` directory:
    ```env
    DATABASE_URL=sqlite:///./omnicopilot.db
    SECRET_KEY=your_generated_jwt_secret
    GOOGLE_CLIENT_ID=your_google_client_id
    GOOGLE_CLIENT_SECRET=your_google_client_secret
    GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
    OPENAI_API_KEY=your_openai_key
    ```
3.  **Run Server**:
    ```bash
    uvicorn main:app --reload
    ```

### 💻 Frontend Setup
1.  **Navigate and Install**:
    ```bash
    cd frontend
    npm install
    ```
2.  **Run Development Server**:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

---

## 🏗️ Project Structure

```text
omnicopilot/
├── backend/
│   ├── auth/           # OAuth2 and JWT authentication logic
│   ├── routes/         # FastAPI endpoint definitions
│   ├── services/       # Core logic for AI tools and external APIs
│   ├── tools/          # AI Tool schemas (Gemini/OpenAI function calling)
│   └── database.py     # SQLAlchemy engine and session setup
├── frontend/
│   ├── src/pages/      # ChatPage, LoginPage, etc.
│   ├── src/components/ # Shared UI elements (Sidebar, Message cards)
│   ├── src/context/    # Auth and Theme state management
│   └── vite.config.js  # Build configuration
└── .gitignore          # Comprehensive rules for project safety
