# ALIS (Adaptive Learning Intelligence System)

## Projektbeschreibung

ALIS ist ein **adaptives Lernsystem**, das personalisierte Lernerfahrungen durch die Orchestrierung mehrerer spezialisierter LLM-Agenten (Architekt, Kurator, Tutor) über einen LangGraph-Workflow ermöglicht. Das System begleitet Lernende von der Zielsetzung über die Materialgenerierung und interaktive Lernphasen bis hin zur Remediation von Wissenslücken und der Generierung von Tests.

Das Projekt ist modular aufgebaut, mit einem Python-Backend, das die Kernlogik und LLM-Interaktionen verwaltet, und einem React-Frontend für die Benutzeroberfläche. Es unterstützt sowohl simulierte als auch reale LLM-API-Aufrufe (Gemini oder OpenAI) und bietet eine grundlegende Protokollierungsfunktion.

## Features

### Backend (Python / LangGraph)
*   **SMART-Lernziel-Verhandlung (P1):** Der **Architekt** hilft bei der Definition messbarer Lernziele.
*   **Lernpfad-Erstellung & -Review (P3):** Der Architekt generiert einen initialen Lernpfad. Benutzer können bekannte Konzepte überspringen.
*   **Materialgenerierung (P4):** Der **Kurator** erstellt Lernmaterial für Konzepte, unter Berücksichtigung des Nutzerprofils.
*   **Interaktive Lernphase & Tutor-Chat (P5):** Der **Tutor** bietet Chat-Unterstützung und adaptive Rückmeldungen.
*   **Dynamische Lücken-Remediation (P5.5):** Bei gemeldeten Wissenslücken diagnostiziert der Tutor die Lücke, und der Architekt passt den Lernpfad dynamisch an.
*   **Testgenerierung (P6):** Der Kurator generiert Verständnisfragen für absolvierte Konzepte.
*   **Pluggable LLM-Provider:** Unterstützung für Google Gemini und OpenAI-Modelle, konfigurierbar über Umgebungsvariablen.
*   **Protokollierung:** Konsolen- und optionale Dateiprotokollierung von Systemereignissen und Nutzerinteraktionen.
*   **Simulierte Dienste:** LLM- und Datenbankinteraktionen (Firestore) sind für die Entwicklung simulierbar.

### Frontend (React)
*   **Phasenbasierte UI:** Klare Darstellung der aktuellen Lernphase (Zielsetzung, Pfad-Review, Lernphase, Testphase).
*   **Lernziel-Eingabe:** UI zur Definition des Lernziels.
*   **Lernpfad-Review:** Interaktive Anzeige des generierten Lernpfads mit Optionen zum Überspringen von Konzepten.
*   **Materialanzeige:** Darstellung des vom Kurator generierten Lernmaterials.
*   **Tutor-Chat:** Interaktives Chat-Interface zur Kommunikation mit dem Tutor.
*   **Remediation-Trigger:** Button zum Melden von Wissenslücken und Initiieren des Remediation-Workflows.
*   **Testanzeige:** Darstellung der generierten Testfragen.

## Architektur

ALIS folgt einer modularen Architektur mit einem klaren Schnitt zwischen Frontend und Backend:

```mermaid
graph TD
    User -- Interagiert mit --> Frontend[React Frontend]
    Frontend -- API-Anfragen --> Backend[Python Backend (Flask)]

    subgraph Backend-Komponenten
        Backend -- Orchestrierung --> LangGraph[LangGraph Workflow]
        LangGraph -- Steuert --> AgentNodes[Agent Nodes (Architekt, Kurator, Tutor)]
        AgentNodes -- Nutzt --> LLMService[LLMService (Gemini / OpenAI)]
        AgentNodes -- Nutzt --> DBService[DBService (Simulated Firestore)]
        AgentNodes -- Nutzt --> LoggingService[LoggingService]
    end

    LLMService -- API Calls --> ExternalLLM[External LLM (Gemini / OpenAI)]
    DBService -- (Optional) --> Firestore[Firestore Database]
    LoggingService -- Schreibt --> Console[Console]
    LoggingService -- Schreibt (Optional) --> LogFile[Log File]

    style Frontend fill:#e0f7fa,stroke:#00bcd4,stroke-width:2px
    style Backend fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style LangGraph fill:#fff8e1,stroke:#ffc107,stroke-width:2px
    style AgentNodes fill:#ffebee,stroke:#f44336,stroke-width:2px
    style LLMService fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style DBService fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style LoggingService fill:#f9fbe7,stroke:#cddc39,stroke-width:2px
    style ExternalLLM fill:#eceff1,stroke:#607d8b,stroke-width:2px
    style Firestore fill:#eceff1,stroke:#607d8b,stroke-width:2px
    style Console fill:#cfd8dc,stroke:#607d8b,stroke-width:1px
    style LogFile fill:#cfd8dc,stroke:#607d8b,stroke-width:1px
```

## Projektstruktur

```
.
├── backend/                                # Python Flask-Backend und LangGraph-Logik
│   ├── agents/                             # LLM-Agenten-Definitionen (Architekt, Kurator, Tutor)
│   ├── config/                             # Konfigurationseinstellungen
│   ├── models/                             # Datenmodelle (ALISState, UserProfile, Goal, LogEntry)
│   ├── services/                           # Externe Dienstintegrationen (LLM, DB, Logging)
│   ├── tests/                              # Unit-Tests für Backend-Komponenten
│   ├── workflows/                          # LangGraph-Workflow-Definition
│   └── app.py                              # Flask-Hauptanwendung
├── frontend/                               # React-Frontend
│   ├── public/                             # Statische Assets
│   ├── src/                                # React-Quellcode
│   │   ├── ALISApp.jsx                     # Haupt-App-Komponente und UI-Logik
│   │   ├── services/                       # Frontend-API-Clients
││   │   └── ...                             # Weitere Frontend-Komponenten/Assets
│   └── ...                                 # Weitere Frontend-Dateien (package.json, vite.config.js etc.)
├── venv/                                   # Python Virtual Environment
├── .env.example                            # Beispiel für Umgebungsvariablen
├── requirements.txt                        # Python-Abhängigkeiten
├── alis.md                                 # Master-Spezifikationsdokument
├── vergleich.md                            # Vergleich mit dem "Learning"-Projekt
└── README.md                               # Dieses Dokument
```

## Erste Schritte

### Voraussetzungen

*   Python 3.8+
*   Node.js 16+ und npm/yarn
*   Git
*   Optional: Google Gemini API Key oder OpenAI API Key

### 1. Repository klonen

```bash
git clone https://github.com/your-username/ALIS.git
cd ALIS
```

### 2. Backend-Setup

1.  **Python Virtual Environment erstellen und aktivieren:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate   # Windows
    ```

2.  **Python-Abhängigkeiten installieren:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Umgebungsvariablen konfigurieren:**
    Erstellen Sie eine `.env`-Datei im Stammverzeichnis des Projekts (neben `requirements.txt`) basierend auf `.env.example`.

    ```ini
    # .env
    # --- Backend Configuration ---
    LLM_PROVIDER=gemini       # oder 'openai'
    
    # Gemini API (wenn LLM_PROVIDER=gemini)
    GEMINI_API_KEY="Ihre_Gemini_API_Key_hier"
    GEMINI_API_URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
    
    # OpenAI API (wenn LLM_PROVIDER=openai)
    OPENAI_API_KEY="Ihre_OpenAI_API_Key_hier"
    OPENAI_MODEL_NAME="gpt-4o-mini" # oder ein anderes Modell wie "gpt-3.5-turbo"
    
    # Firestore (simuliert für Entwicklung)
    USE_FIRESTORE_SIMULATOR=true # Setzen Sie auf 'false' für reale Firestore-Verbindung
    # FIREBASE_CREDENTIALS_PATH="/path/to/your/firebase-adminsdk.json" # Nur wenn USE_FIRESTORE_SIMULATOR=false
    
    # Server & CORS
    HOST=0.0.0.0
    PORT=5000
    DEBUG=true
    CORS_ORIGINS=http://localhost:3000,http://localhost:5173 # Frontend-URLs
    
    # LLM Standard-Parameter
    DEFAULT_TEMPERATURE=0.7
    DEFAULT_MAX_TOKENS=2048
    ```
    Ersetzen Sie die Platzhalter für API-Schlüssel. Wenn Sie einen realen LLM-Provider nutzen möchten, stellen Sie sicher, dass der entsprechende API-Schlüssel gesetzt ist und `LLM_PROVIDER` korrekt konfiguriert ist.

4.  **Backend starten:**
    ```bash
    cd backend
    python app.py
    ```
    Das Backend sollte auf `http://localhost:5000` (oder dem in `.env` konfigurierten Port) laufen.

### 3. Frontend-Setup

1.  **Node.js-Abhängigkeiten installieren:**
    ```bash
    cd frontend
    npm install
    # oder yarn install
    ```

2.  **Frontend starten:**
    ```bash
    npm run dev
    # oder yarn dev
    ```
    Das Frontend sollte unter `http://localhost:5173` (oder einem anderen, von Vite zugewiesenen Port) verfügbar sein.

## Nutzung

Öffnen Sie Ihr Frontend im Browser (`http://localhost:5173`):
1.  **Ziel-Kontrakt (P1):** Geben Sie Ihr Lernziel ein und lassen Sie den **Architekten** einen SMART-Vertrag erstellen.
2.  **Lernpfad-Review (P3):** Prüfen Sie den generierten Lernpfad und markieren Sie Konzepte, die Sie bereits beherrschen.
3.  **Lernphase (P5):** Nehmen Sie das generierte Material auf und interagieren Sie mit dem **Tutor** über den Chat.
4.  **Remediation (P5.5):** Melden Sie Wissenslücken, um den Lernpfad dynamisch anpassen zu lassen.
5.  **Test (P6):** Bestätigen Sie das Konzept als verstanden, um einen Test zu generieren.

## Tests ausführen

Um die Backend-Tests auszuführen, stellen Sie sicher, dass Ihr Virtual Environment aktiviert ist, navigieren Sie zum Projekt-Stammverzeichnis und führen Sie Pytest aus:

```bash
source venv/bin/activate
PYTHONPATH=. pytest backend/tests/
```

## Zukünftige Erweiterungen & Offene Punkte

Basierend auf den Analysen (`alis_analysis.md`, `SPEC_COMPARISON.md`, `vergleich.md`) sind folgende Punkte für die Weiterentwicklung relevant:

*   **Vollständige Implementierung der Datenmodelle:** Integration aller Felder gemäß `alis.md` in `UserProfile`, `Goal` und `LogEntry`.
*   **Persistenz:** Anbindung an eine reale Firestore-Datenbank zur Speicherung des Nutzerfortschritts, der Lernpfade und der Log-Einträge.
*   **Umfassendes Logging:** Speicherung der `LogEntry`-Daten in Firestore und Erweiterung um detailliertere Metriken (z.B. `emotionFeedback`, `testScore`, `kognitiveDiskrepanz`).
*   **P7 (Adaption):** Implementierung der automatischen Progression basierend auf Test-Scores und der Anpassung des Lernpfads.
*   **Integration des "Learning"-Projekts:** Potenzielle Übernahme der interaktiven Graphen-UI, der PCG-Extraktionspipeline, des sokratischen Dialogs mit Live-Coding und der RAG-Fähigkeiten zur weiteren Verbesserung von ALIS.
*   **Authentifizierung:** Implementierung eines Benutzersystems.
*   **Fehlerbehandlung:** Robuste Fehlerbehandlung für API-Aufrufe.

---

Viel Spaß beim Lernen mit ALIS!
