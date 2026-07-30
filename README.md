# AI Root Cause Investigator

## Overview

AI Root Cause Investigator is an AI-powered application that analyzes uploaded documents, logs, and datasets to identify the most likely root causes of failures or incidents.

---

## Features

- PDF Upload
- Document Parsing
- Embedding Generation
- Vector Search
- AI Root Cause Analysis
- Interactive Dashboard
- Report Generation

---

## Tech Stack

### Backend
- FastAPI
- Python
- Loguru
- Pydantic

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui

### AI
- Groq API
- LangGraph
- FAISS

---

## Installation

### Backend

```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```