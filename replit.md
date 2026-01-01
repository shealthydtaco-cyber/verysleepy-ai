# Ethereal AI - Voice & Chat Interface

## Overview
An AI-powered voice and chat assistant with a fluid, ethereal visual interface using WebGL animations.

## Project Structure
- **frontend/**: Next.js 16 React application with Tailwind CSS
  - Voice and chat interfaces with 3D orb visualization
  - Uses Three.js for WebGL effects
  - Port: 5000
- **backend/**: Python FastAPI server
  - AI query processing, memory management, TTS/STT
  - Port: 8000 (not currently running)

## Running the Application
- Frontend runs via the "Frontend" workflow on port 5000
- Backend requires additional dependencies (voice, TTS modules) to fully function

## Environment Variables
- `NEXT_PUBLIC_BACKEND_URL`: Backend API URL for frontend to connect

## Tech Stack
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS v4, Three.js
- Backend: Python 3.11, FastAPI, Uvicorn
