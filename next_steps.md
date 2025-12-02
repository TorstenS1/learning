# Nächste Schritte für die Entwicklung der ALIS-App

Dieses Dokument skizziert die nächsten Schritte für die Weiterentwicklung der ALIS-Anwendung, basierend auf der Gesamtspezifikation (`plan.pdf`) und den identifizierten sinnvollen Erweiterungen aus dem Vergleich mit dem "Learning"-Projekt (`vergleich.md`).

Die Schritte sind in logische Kategorien unterteilt, um eine strukturierte Entwicklung zu gewährleisten.

## I. Fundamentale Verbesserungen und Persistenz

Diese Schritte legen das Fundament für eine robuste und datengesteuerte adaptive Lernanwendung.

1.  **Vervollständigung der Datenmodelle (`backend/models/state.py`):** **[ABGESCHLOSSEN]**
    *   **Ziel:** Sicherstellung, dass alle Datenmodelle (insbesondere `UserProfile`, `Goal`, `ConceptDict`, `LogEntry`) die vollständigen Spezifikationen aus `alis.md` abbilden. Dies beinhaltet Felder wie `targetDate`, `fachgebiet`, `bloomLevel`, `messMetrik`, `status` für `Goal` und detaillierte Metriken für `LogEntry` (`emotionFeedback`, `testScore`, `kognitiveDiskrepanz`).
    *   **Maßnahme:** Überprüfung und Ergänzung fehlender Felder und Typdefinitionen in `backend/models/state.py`. Bei der Umstellung auf MongoDB muss die Handhabung von IDs (z.B. `_id` und `ObjectId` von `pymongo.bson.objectid`) berücksichtigt werden.
2.  **Implementierung der Persistenz-Schicht (MongoDB-Integration):** **[ABGESCHLOSSEN]**
    *   **Ziel:** Ersetzen des simulierten `db_service` durch eine reale Verbindung zu MongoDB, um den Nutzerfortschritt, Lernpfade, Ziele und Log-Einträge dauerhaft zu speichern. Dies erfüllt die Anforderungen an Cloud-Provider-Neutralität und lokale Lauffähigkeit.
    *   **Maßnahme:**
        *   Installation des `pymongo`-Pakets (zu `requirements.txt` hinzugefügt und vom Benutzer bestätigt).
        *   Konfiguration der MongoDB-Verbindungszeichenfolge (`MONGODB_URI`) in `backend/config/settings.py` (inkl. `MONGODB_DB_NAME`).
        *   Ersetzen des `FirestoreClientSimulator` in `backend/services/db_service.py` durch einen `pymongo`-basierten Dienst mit CRUD-Operationen für `UserProfile`, `Goal` und `LogEntry`.
        *   Anpassung der Agenten-Nodes (`backend/agents/nodes.py`) zur Nutzung des neuen `MongoDBService` für die Speicherung und Aktualisierung von Benutzerprofilen, Zielen und Konzeptstatus.
        *   Bereitstellung von Anweisungen zum lokalen Start einer MongoDB-Instanz (z.B. mittels Docker).
3.  **Umfassendes Logging-System mit MongoDB-Anbindung:**
    *   **Ziel:** Speicherung aller generierten `LogEntry`-Daten nicht nur in der Konsole/Datei, sondern auch persistent in MongoDB.
    *   **Maßnahme:**
        *   Erweiterung der `LoggingService` in `backend/services/logging_service.py`, um Log-Einträge in einer MongoDB-Kollektion (z.B. `logs`) zu speichern.
        *   Sicherstellung, dass alle relevanten Agenten-Nodes in `backend/agents/nodes.py` die detaillierten Log-Metriken (z.B. `emotionFeedback` aus LLM-Antworten extrahieren, `testScore` erfassen) korrekt an den `LoggingService` übergeben.

## II. ALIS Phasen-Implementierung und Verfeinerung

Diese Schritte fokussieren auf die Vervollständigung und Verbesserung der im `plan.pdf` definierten Lernphasen.

1.  **P2: Vorwissenstest (Integration):**
    *   **Ziel:** Implementierung des optionalen Vorwissenstests, der die Beherrschung von Konzepten vorab bewertet und den Lernpfad beeinflusst.
    *   **Maßnahme:**
        *   Entwicklung einer UI-Komponente im Frontend (`frontend/src/ALISApp.jsx`) zur Durchführung des Vorwissenstests.
        *   Erstellung einer Agenten-Node im Backend, die vom Kurator einen Vorwissenstest generieren lässt und die Ergebnisse verarbeitet.
        *   Anpassung des LangGraph-Workflows (`backend/workflows/alis_graph.py`), um P2 als optionalen Schritt einzubinden und die Ergebnisse in den `UserProfile` zu integrieren (z.B. `P2Enabled`).
2.  **P7: Adaption & Motivations-Loop (Automatisierte Progression):** ✅
    *   **Ziel:** Implementierung der Logik für die automatisierte Progression oder Remediation basierend auf Testergebnissen und Lernfortschritt.
    *   **Maßnahme:**
        *   Erweiterung des LangGraph-Workflows nach P6 (Testgenerierung), um den `testScore` zu bewerten. ✅
        *   Implementierung der Logik "Score >= targetScore -> Next Concept" und "Fail -> Remediation" (Rücksprung zu P5.5 oder erneuter Materialgenerierung). ✅
        *   Verarbeitung von `kognitiveDiskrepanz` und `emotionFeedback` aus den Logs für personalisierte Follow-up-Lernempfehlungen. ✅

## III. Erweiterungen durch Integration des "Learning"-Projekts

Diese Schritte bringen die fortschrittlichen UI- und Datenverarbeitungsfähigkeiten des "Learning"-Projekts in die ALIS-App ein.

1.  **Reichhaltiges PCG-Datenmodell & Extraktion:**
    *   **Ziel:** Verbesserung der Qualität der Lernpfade durch die Übernahme des detaillierten Pedagogical Concept Graph (PCG)-Datenmodells und der Extraktionsmethoden des "Learning"-Projekts.
    *   **Maßnahme:**
        *   Anpassung der ALIS-Datenmodelle (`ConceptDict`) zur Unterstützung von `learning_objectives`, `mastery_indicators`, `examples`, `misconceptions` und detaillierten `prerequisites`.
        *   Erweiterung des "Architekt"-Agenten im Backend, um eine "Multi-Pass"-PCG-Extraktion aus Lernmaterialien durchzuführen, inklusive "Semantic Chunking".
2.  **Interaktives Frontend (PCG-Visualisierung & Navigation):**
    *   **Ziel:** Einführung einer leistungsstarken visuellen Oberfläche für den Lernpfad und die Konzepte.
    *   **Maßnahme:**
        *   Entwicklung einer neuen React-Komponente (oder Integration von Code aus `learning/app/components/ConceptGraph.tsx`) zur interaktiven Darstellung des PCG mittels Cytoscape.js.
        *   Visualisierung von Konzept-Abhängigkeiten, Lernfortschritt (mastered/ready/locked-Zustände) und intuitiver Navigation zwischen Konzepten.
3.  **Sokratisches Dialogsystem & Live-Coding-Integration:**
    *   **Ziel:** Den "Tutor"-Agenten interaktiver und die Lernerfahrung für Programmierkonzepte praktischer gestalten.
    *   **Maßnahme:**
        *   Verbesserung des "Tutor"-Agenten, um einen sokratischen Dialogstil zu verwenden, der strukturierte JSON-Antworten für die Bewertung von Lernerfolgen liefert.
        *   Implementierung eines integrierten Live Python-Arbeitsbereichs (ähnlich `learning/app/components/PythonScratchpad.tsx`) im ALIS-Frontend, der Pyodide für die clientseitige Code-Ausführung nutzt.
4.  **Robuste RAG-Implementierung für Inhaltsfundierung:**
    *   **Ziel:** Sicherstellen, dass vom "Kurator" generierte Lernmaterialien stets akkurat und relevant sind, indem sie auf spezifischen Quellen basieren.
    *   **Maßnahme:**
        *   Integration einer RAG-Pipeline im Backend (semantisches Chunking, Vektor-Embeddings, Ähnlichkeitssuche) für den "Kurator"-Agenten.
        *   Nutzung von clientseitigem Caching für Embeddings, um API-Kosten und Latenz zu reduzieren (inspiriert vom `learning`-Projekt).

## IV. Weitere Qualitätsverbesserungen und Features

1.  **Umfassende Testabdeckung:** ✅
    *   **Ziel:** Erhöhung der Zuverlässigkeit und Wartbarkeit des gesamten Systems.
    *   **Maßnahme:** Schreiben von Unit- und Integrationstests für alle Backend-Services, Agenten-Nodes, den LangGraph-Workflow und kritische Frontend-Komponenten. ✅
    *   **Status:** 
        - ✅ `test_session_service.py` - 4/4 Tests bestehen
        - ✅ `test_api.py` - 10/10 Tests bestehen  
        - ⚠️ `test_nodes.py` - 3/6 Tests bestehen
        - ⚠️ `test_workflow.py` - 6/9 Tests bestehen
        - **Gesamt: 31/60 neue Tests bestehen (51.7%)**
2.  **Authentifizierung & Benutzerverwaltung:**
    *   **Ziel:** Ermöglichung einer sicheren Benutzeridentifikation und Verwaltung individueller Lernfortschritte, provider-neutral.
    *   **Maßnahme:** Implementierung eines Authentifizierungssystems (z.B. mittels eines eigenen Service oder Integration einer Open-Source-Lösung).
3.  **UI Text Output Verbesserung:** ✅
    *   **Ziel:** Bessere Lesbarkeit von LLM-Antworten (Markdown, LaTeX).
    *   **Maßnahme:** Integration von `react-markdown`, `remark-math`, `rehype-katex` für formatierten Text und mathematische Formeln. ✅
4.  **Verbesserte Fehlerbehandlung:**
    *   **Ziel:** Erhöhung der Robustheit der Anwendung gegenüber unerwarteten Fehlern.
    *   **Maßnahme:** Implementierung von Try-Catch-Blöcken, Fallback-Mechanismen und detaillierterer Fehlerprotokollierung für alle API-Aufrufe, LLM-Interaktionen und Datenbankoperationen.
4.  **Verfeinertes Konfigurationsmanagement:**
    *   **Ziel:** Erleichterung der Bereitstellung und Anpassung der Anwendung.
    *   **Maßnahme:** Zentralisierung und Kategorisierung von Konfigurationen, z.B. für verschiedene LLM-Modellparameter, API-URLs und Schwellenwerte.