# Internationalisierung (i18n) Implementation Guide

## Übersicht
Das Frontend wurde für Mehrsprachigkeit vorbereitet. Deutsch und Englisch sind verfügbar.

## Struktur
```
frontend/src/i18n/
├── index.js    # i18n utilities
├── de.js       # German translations
└── en.js       # English translations
```

## Integration in ALISApp.jsx

### 1. Import hinzufügen (am Anfang der Datei)
```javascript
import { getTranslations, getStoredLanguage } from './i18n';
```

### 2. State für Sprache hinzufügen
```javascript
const [language, setLanguage] = useState(getStoredLanguage());
const t = getTranslations(language);
```

### 3. Language Switcher Component hinzufügen
```javascript
const LanguageSwitcher = () => (
    <div className="fixed top-4 right-4 z-50">
        <select 
            value={language}
            onChange={(e) => {
                setLanguage(e.target.value);
                localStorage.setItem('alis_language', e.target.value);
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white shadow-sm"
        >
            <option value="de">🇩🇪 Deutsch</option>
            <option value="en">🇬🇧 English</option>
        </select>
    </div>
);
```

### 4. Texte ersetzen - Beispiele

#### Vorher:
```javascript
<h1 className="text-3xl font-extrabold text-indigo-700 mb-4">
    ALIS: Ziel-Kontrakt (P1)
</h1>
```

#### Nachher:
```javascript
<h1 className="text-3xl font-extrabold text-indigo-700 mb-4">
    {t.p1.title}
</h1>
```

#### Vorher:
```javascript
<button>SMART-Vertrag erstellen</button>
```

#### Nachher:
```javascript
<button>{t.p1.buttonSubmit}</button>
```

## Verfügbare Übersetzungen

### P1 (Goal Setting)
- `t.p1.title` - Titel
- `t.p1.description` - Beschreibung
- `t.p1.placeholder` - Placeholder
- `t.p1.buttonSubmit` - Button Text
- `t.p1.buttonSubmitting` - Button Text (loading)

### P2 (Prior Knowledge)
- `t.p2.choiceTitle` - Titel der Auswahl
- `t.p2.choiceDescription` - Beschreibung
- `t.p2.choiceYes` - "Ja" Button
- `t.p2.choiceNo` - "Nein" Button
- `t.p2.testTitle` - Test Titel
- `t.p2.submitButton` - Submit Button

### P3 (Path Review)
- `t.p3.title` - Titel
- `t.p3.description` - Beschreibung
- `t.p3.conceptStatus.open` - Status "Offen"
- `t.p3.conceptStatus.mastered` - Status "Beherrscht"
- `t.p3.markAsKnown` - Button Text
- `t.p3.startLearning` - Start Button

### P5 (Learning)
- `t.p5.title` - Titel
- `t.p5.tutorChat` - Chat Titel
- `t.p5.chatPlaceholder` - Chat Placeholder
- `t.p5.reportGap` - Gap Report Button
- `t.p5.understood` - Verstanden Button

### P6 (Test)
- `t.p6.title` - Titel
- `t.p6.description` - Beschreibung
- `t.p6.submitTest` - Submit Button
- `t.p6.generating` - Generierungs-Text
- `t.p6.evaluating` - Bewertungs-Text

### P7 (Evaluation)
- `t.p7.progression.title` - Titel
- `t.p7.progression.nextConcept` - Weiter Button
- `t.p7.goalComplete.title` - Ziel erreicht Titel
- `t.p7.goalComplete.newGoal` - Neues Ziel Button
- `t.p7.remediation.title` - Wiederholung Titel
- `t.p7.detailedEvaluation` - Detaillierte Auswertung

### Common
- `t.common.loading` - "Lädt..."
- `t.common.error` - "Fehler"
- `t.common.back` - "Zurück"
- `t.common.next` - "Weiter"

## Nächste Schritte

Um die vollständige Integration durchzuführen, müssen alle hardcodierten Texte in `ALISApp.jsx` durch die entsprechenden `t.*` Referenzen ersetzt werden.

Dies betrifft:
1. Alle `<h1>`, `<h2>`, `<h3>` Titel
2. Alle `<p>` Beschreibungstexte
3. Alle Button-Texte
4. Alle Placeholder-Texte
5. Alle Status-Texte

Die Sprachumschaltung erfolgt automatisch basierend auf:
1. Browser-Sprache (beim ersten Laden)
2. Gespeicherte Präferenz in localStorage
3. Manueller Wechsel über den Language Switcher
