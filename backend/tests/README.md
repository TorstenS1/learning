# ALIS Backend Tests

Umfassende Test-Suite für das ALIS Backend.

## Struktur

```
backend/tests/
├── TEST_COVERAGE.md          # Detaillierter Status-Report
├── test_api.py               # API Endpoint Tests ✅
├── test_session_service.py   # Session Management Tests ✅
├── test_nodes.py             # Agent Node Tests ⚠️
├── test_workflow.py          # Workflow Tests ⚠️
├── test_db_service.py        # Database Tests (existing)
└── test_llm_service.py       # LLM Service Tests (existing)
```

## Quick Start

### Alle Tests ausführen

```bash
PYTHONPATH=. venv/bin/python -m pytest backend/tests/ -v
```

### Nur erfolgreiche Tests

```bash
# Session Management (4/4 ✅)
PYTHONPATH=. venv/bin/python -m pytest backend/tests/test_session_service.py -v

# API Endpoints (10/10 ✅)
PYTHONPATH=. venv/bin/python -m pytest backend/tests/test_api.py -v
```

### Mit Coverage Report

```bash
PYTHONPATH=. venv/bin/python -m pytest backend/tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

## Test-Kategorien

### ✅ Unit Tests
- **Session Service:** Speichern, Laden, Auflisten von Sessions
- **Agent Nodes:** create_goal_path, generate_material
- **Workflow Routing:** should_progress, should_remediate

### ✅ Integration Tests
- **API Endpoints:** Health, Goal Creation, Material, Test Evaluation
- **Session Management:** Save, Load, List via API
- **Error Handling:** 404, 500, Missing Fields

### ⚠️ In Arbeit
- **Node Tests:** evaluate_test, process_chat (Mock-Probleme)
- **Workflow Execution:** End-to-End Flows
- **Database Tests:** MongoDB-Integration

## Mocking

Die Tests verwenden `unittest.mock` für:
- **LLM Service:** Simulierte LLM-Antworten
- **Database Service:** In-Memory MongoDB-Operationen
- **Workflow Nodes:** Isolierte Node-Tests

### Beispiel: LLM Mock

```python
@pytest.fixture
def mock_llm_service():
    with patch('backend.agents.nodes.get_llm_service') as mock:
        mock_llm = MagicMock()
        mock_llm.call.return_value = '{"score": 85, "passed": true}'
        mock.return_value = mock_llm
        yield mock_llm
```

## Best Practices

1. **Isolation:** Jeder Test ist unabhängig
2. **Fixtures:** Wiederverwendbare Test-Daten
3. **Mocking:** Externe Abhängigkeiten werden gemockt
4. **Assertions:** Klare, spezifische Assertions
5. **Documentation:** Jeder Test hat einen Docstring

## Troubleshooting

### Import Errors

```bash
# Stelle sicher, dass PYTHONPATH gesetzt ist
export PYTHONPATH=.
```

### MongoDB Connection Errors

```bash
# Starte MongoDB lokal oder verwende Mocks
docker run -d -p 27017:27017 mongo:latest
```

### Missing Dependencies

```bash
# Installiere Test-Dependencies
pip install pytest pytest-cov pytest-flask pytest-anyio
```

## Continuous Integration

Die Tests sind CI/CD-ready und können in GitHub Actions, Jenkins, etc. integriert werden:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: PYTHONPATH=. pytest backend/tests/ -v
```

## Weitere Informationen

Siehe `TEST_COVERAGE.md` für detaillierte Informationen über:
- Test-Status pro Datei
- Bekannte Probleme
- Nächste Schritte
- Coverage-Metriken
