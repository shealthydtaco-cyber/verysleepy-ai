# Local Setup Guide - Ethereal AI

This guide explains how to run Ethereal AI on your local machine.

## Prerequisites
- **Node.js**: v20 or higher
- **Python**: 3.11 or higher
- **Git**

## Project Structure
- `frontend/`: Next.js React application
- `backend/`: FastAPI Python server

---

## 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   python api.py
   ```
   The backend will run on `http://localhost:8000`.

---

## 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   Create a `.env.local` file in the `frontend` folder:
   ```env
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend will run on `http://localhost:3000` (or `http://localhost:5000` depending on your `package.json` configuration).

---

## 3. Running as an Electron App (Optional)

If you are using the Electron wrapper:
1. Ensure the backend is running.
2. In the root directory or Electron-specific directory, run:
   ```bash
   npm install
   npm start
   ```

## Troubleshooting
- **CORS Issues**: Ensure the backend `api.py` has `allow_origins=["*"]` or includes your local frontend URL.
- **Port Conflicts**: If port 5000 or 8000 is in use, you can change them in `package.json` (frontend) or `api.py` (backend).
