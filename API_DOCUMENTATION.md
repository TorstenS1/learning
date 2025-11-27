# ALIS Backend API Documentation

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Health Check
**GET** `/api/health`

Check if the server is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "ALIS Backend",
  "version": "1.0.0",
  "simulation_mode": true
}
```

---

### 2. Start Goal Setting (P1/P3)
**POST** `/api/start_goal`

Create a SMART learning goal and generate initial learning path.

**Request Body:**
```json
{
  "userId": "user123",
  "userInput": "Ich möchte lernen, wie man ein KI-basiertes Empfehlungssystem mit Python implementiert.",
  "userProfile": {
    "stylePreference": "Analogien-basiert",
    "paceWPM": 180
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "userId": "user123",
    "goalId": "G-TEMP-001",
    "llm_output": "### LERNZIEL-VERTRAG\n...",
    "path_structure": [
      {
        "id": "K1",
        "name": "Python/Pandas-Grundlagen",
        "status": "Übersprungen",
        "expertiseSource": "P3 Experte",
        "requiredBloomLevel": 2
      },
      {
        "id": "K2",
        "name": "Einführung in Matrix-Faktorisierung",
        "status": "Aktiv",
        "requiredBloomLevel": 3
      }
    ],
    "current_concept": {
      "id": "K2",
      "name": "Einführung in Matrix-Faktorisierung",
      "status": "Aktiv",
      "requiredBloomLevel": 3
    },
    "user_profile": {
      "stylePreference": "Analogien-basiert",
      "paceWPM": 180
    }
  }
}
```

---

### 3. Get Learning Material (P4)
**POST** `/api/get_material`

Generate learning material for the current concept.

**Request Body:**
```json
{
  "userId": "user123",
  "goalId": "G-TEMP-001",
  "pathStructure": [...],
  "currentConcept": {
    "id": "K2",
    "name": "Einführung in Matrix-Faktorisierung",
    "requiredBloomLevel": 3
  },
  "userProfile": {
    "stylePreference": "Analogien-basiert",
    "paceWPM": 180
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "llm_output": "### MATERIAL\n**Einführung in Matrix-Faktorisierung**\n...",
    "path_structure": [...],
    "current_concept": {...}
  }
}
```

---

### 4. Chat with Tutor (P5)
**POST** `/api/chat`

Send a message to the tutor for help or questions.

**Request Body:**
```json
{
  "userId": "user123",
  "goalId": "G-TEMP-001",
  "userInput": "Ich verstehe nicht, wie Matrix-Faktorisierung funktioniert.",
  "currentConcept": {
    "id": "K2",
    "name": "Einführung in Matrix-Faktorisierung"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "llm_output": "Das ist eine gute Frage! Lass mich dir helfen..."
  }
}
```

---

### 5. Diagnose Knowledge Gap (P5.5 - Part 1)
**POST** `/api/diagnose_luecke`

Trigger gap diagnosis when user reports missing foundation.

**Request Body:**
```json
{
  "userId": "user123",
  "goalId": "G-TEMP-001",
  "pathStructure": [...],
  "currentConcept": {
    "id": "K2",
    "name": "Einführung in Matrix-Faktorisierung"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "llm_output": "Welches Schlüsselkonzept fehlt Ihnen genau?",
    "remediation_needed": true
  }
}
```

---

### 6. Perform Path Surgery (P5.5 - Part 2)
**POST** `/api/perform_remediation`

Insert missing concept into learning path.

**Request Body:**
```json
{
  "userId": "user123",
  "goalId": "G-TEMP-001",
  "userInput": "Grundlagen der linearen Algebra",
  "pathStructure": [...],
  "currentConcept": {...},
  "remediationNeeded": true
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "llm_output": "Der Architekt hat das neue Kapitel 'Grundlagen der linearen Algebra' eingefügt.",
    "path_structure": [
      {
        "id": "N-1234567890",
        "name": "Grundlagen der linearen Algebra",
        "status": "Offen",
        "expertiseSource": "P5.5 Remediation",
        "requiredBloomLevel": 1
      },
      ...
    ],
    "current_concept": {
      "id": "N-1234567890",
      "name": "Grundlagen der linearen Algebra",
      "status": "Offen"
    },
    "remediation_needed": false
  }
}
```

---

### 7. Generate Test Questions (P6)
**POST** `/api/generate_test`

Generate comprehension test questions for current concept.

**Request Body:**
```json
{
  "userId": "user123",
  "goalId": "G-TEMP-001",
  "currentConcept": {
    "id": "K2",
    "name": "Einführung in Matrix-Faktorisierung",
    "requiredBloomLevel": 3
  },
  "userProfile": {
    "stylePreference": "Analogien-basiert"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "llm_output": "### TESTFRAGEN\n\n**Frage 1 (Multiple Choice)**\n..."
  }
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "status": "error",
  "message": "Error description here"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (missing required fields)
- `404` - Endpoint not found
- `500` - Internal server error

---

## CORS Configuration

The API allows requests from:
- `http://localhost:3000` (Create React App default)
- `http://localhost:5173` (Vite default)

Additional origins can be configured in `.env`:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://your-domain.com
```

---

## Testing with cURL

### Health Check
```bash
curl http://localhost:5000/api/health
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

---

## Running the Server

### Quick Start
```bash
./start_backend.sh
```

### Manual Start
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run server
python backend/app.py
```

The server will start on `http://localhost:5000` by default.
