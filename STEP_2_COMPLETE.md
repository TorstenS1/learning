# ALIS Backend API - Step 2 Complete ✅

## Overview
Successfully created a Flask REST API wrapper for the ALIS backend, providing HTTP endpoints for the React frontend.

## Files Created

### 1. **backend/app.py** (Main Flask Application)
- Complete REST API with 7 endpoints
- CORS configuration for frontend integration
- Error handling middleware
- Request/response validation
- Comprehensive logging

### 2. **.env.example** (Environment Template)
- API key configuration
- Server settings
- CORS origins
- LLM parameters

### 3. **requirements.txt** (Python Dependencies)
- Flask and flask-cors
- LangGraph and LangChain
- Google Cloud/Firebase
- Development tools (pytest, mypy, black)

### 4. **.gitignore** (Version Control)
- Python artifacts
- Virtual environments
- Environment files
- IDE configurations

### 5. **start_backend.sh** (Startup Script)
- Automated environment setup
- Dependency installation
- Server startup

### 6. **API_DOCUMENTATION.md** (API Reference)
- Complete endpoint documentation
- Request/response examples
- cURL testing commands
- Error handling guide

## API Endpoints

| Endpoint | Method | Purpose | Phase |
|----------|--------|---------|-------|
| `/api/health` | GET | Health check | - |
| `/api/start_goal` | POST | Create SMART goal & path | P1/P3 |
| `/api/get_material` | POST | Generate learning material | P4 |
| `/api/chat` | POST | Chat with tutor | P5 |
| `/api/diagnose_luecke` | POST | Start gap diagnosis | P5.5-1 |
| `/api/perform_remediation` | POST | Perform path surgery | P5.5-2 |
| `/api/generate_test` | POST | Generate test questions | P6 |

## Key Features

### ✅ **CORS Support**
- Configured for React dev servers (ports 3000, 5173)
- Customizable via environment variables
- Handles preflight OPTIONS requests

### ✅ **Error Handling**
- Try/catch blocks in all endpoints
- Detailed error logging
- User-friendly error messages
- HTTP status codes (400, 404, 500)

### ✅ **Request Validation**
- Checks for required fields
- Returns 400 Bad Request if missing
- Clear error messages

### ✅ **Service Integration**
- Uses refactored service layer
- LLM service for AI responses
- Database service for persistence
- Workflow orchestration via LangGraph

### ✅ **Development Friendly**
- Simulation mode by default
- Hot reload with Flask debug mode
- Comprehensive logging
- Easy testing with cURL

## Architecture

```
Frontend (React)
    │
    │ HTTP POST
    ▼
Flask API (backend/app.py)
    │
    ├─► LLM Service ──► Gemini API (or simulation)
    │
    ├─► DB Service ──► Firestore (or simulation)
    │
    └─► Workflow ──► LangGraph
            │
            └─► Agent Nodes
                ├─► Architekt
                ├─► Kurator
                └─► Tutor
```

## How to Run

### Quick Start
```bash
./start_backend.sh
```

### Manual Setup
```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit .env with your API keys

# 4. Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 5. Run server
python backend/app.py
```

Server will start on: **http://localhost:5000**

## Testing the API

### Health Check
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ALIS Backend",
  "version": "1.0.0",
  "simulation_mode": true
}
```

### Start Goal
```bash
curl -X POST http://localhost:5000/api/start_goal \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test_user",
    "userInput": "Ich möchte Python Machine Learning lernen"
  }'
```

### Chat
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test_user",
    "userInput": "Was ist supervised learning?",
    "currentConcept": {"id": "K1", "name": "ML Basics"}
  }'
```

## Environment Variables

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Key variables:
- `GEMINI_API_KEY`: Your Gemini API key (optional in simulation mode)
- `USE_FIRESTORE_SIMULATOR`: Set to `true` for development
- `PORT`: Server port (default: 5000)
- `CORS_ORIGINS`: Allowed frontend origins

## Next Steps

**Step 3**: Update React Frontend
- Replace `simulateApiCall()` with real `fetch()` calls
- Update API endpoint URLs
- Add error handling
- Test integration

## Benefits

✅ **RESTful Design**: Standard HTTP methods and status codes
✅ **Type Safety**: Request validation and error handling
✅ **CORS Ready**: Frontend can connect immediately
✅ **Well Documented**: API docs with examples
✅ **Easy Testing**: cURL commands provided
✅ **Production Ready**: Error handling, logging, CORS
✅ **Flexible**: Simulation mode for development

## File Structure After Step 2

```
learning/
├── backend/
│   ├── __init__.py
│   ├── app.py                    # ← NEW: Flask REST API
│   ├── config/
│   │   └── settings.py
│   ├── models/
│   │   └── state.py
│   ├── services/
│   │   ├── db_service.py
│   │   └── llm_service.py
│   ├── agents/
│   │   ├── prompts.py
│   │   └── nodes.py
│   └── workflows/
│       └── alis_graph.py
├── .env.example                  # ← NEW: Environment template
├── .gitignore                    # ← NEW: Git ignore rules
├── requirements.txt              # ← NEW: Python dependencies
├── start_backend.sh              # ← NEW: Startup script
├── API_DOCUMENTATION.md          # ← NEW: API reference
├── ALISApp.jsx                   # Frontend (to be updated)
└── alis_backend.py               # Original (can be archived)
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -ti:5000 | xargs kill -9

# Or change port in .env
PORT=5001
```

### Module Not Found
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /home/torsten/dev/my-projects/learning
python backend/app.py
```

### CORS Errors
- Check `CORS_ORIGINS` in `.env`
- Ensure frontend URL is included
- Restart server after changing `.env`

---

**Status**: ✅ Step 2 Complete - Flask API Ready
**Next**: Step 3 - Update React Frontend to use real API
