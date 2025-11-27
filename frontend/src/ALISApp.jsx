import React, { useState, useEffect } from 'react';
import { Loader2, Zap, LayoutList, BookOpen, MessageCircle, AlertTriangle, ArrowRight } from 'lucide-react';
import alisAPI from './services/alisAPI';

// ==============================================================================
// 1. BACKEND API INTEGRATION
// ==============================================================================

// ==============================================================================
// 2. HAUPTKOMPONENTE
// ==============================================================================

const App = () => {
    const [phase, setPhase] = useState('P1_GOAL_SETTING');
    const [goalInput, setGoalInput] = useState('');
    const [state, setState] = useState({
        userId: 'ALIS-User-ID-12345',
        goalId: null,
        pathStructure: [],
        currentConcept: null,
        llmOutput: "Definieren Sie Ihr Lernziel, um den Architekten zu starten.",
        userInput: '',
        remediationNeeded: false,
        userProfile: { stylePreference: 'Analogien-basiert', paceWPM: 180 },
        loading: false,
        tutorChat: [],
    });

    const updateState = (updates) => setState(s => ({ ...s, ...updates }));

    // ==============================================================================
    // 3. WICHTIGE WORKFLOW-FUNKTIONEN
    // ==============================================================================

    const startGoalSetting = async () => {
        if (!goalInput) return;
        updateState({ loading: true, llmOutput: 'Architekt wird kontaktiert...' });

        try {
            const result = await alisAPI.startGoal(
                state.userId,
                goalInput,
                state.userProfile
            );

            updateState({
                loading: false,
                goalId: result.data.goalId || 'G-TEMP-001',
                llmOutput: result.data.llm_output,
                pathStructure: result.data.path_structure,
                currentConcept: result.data.current_concept,
            });
            setPhase('P3_PATH_REVIEW');
        } catch (error) {
            updateState({
                loading: false,
                llmOutput: `Fehler beim Kontaktieren des Architekten: ${error.message}`
            });
        }
    };

    const confirmPathAndStartLearning = async () => {
        // Hier würde die Logik zur Speicherung der P3 Skips erfolgen.
        if (!state.currentConcept) {
            updateState({ llmOutput: 'Fehler: Es konnte kein aktives Konzept gefunden werden.' });
            return;
        }
        updateState({ loading: true, llmOutput: 'Kurator generiert Material...' });
        setPhase('P4_MATERIAL_GENERATION');

        try {
            const result = await alisAPI.getMaterial(
                state.userId,
                state.goalId,
                state.pathStructure,
                state.currentConcept,
                state.userProfile
            );

            updateState({
                loading: false,
                llmOutput: result.data.llm_output,
                tutorChat: [{ sender: 'System', message: 'Willkommen in der Lernphase! Fragen Sie mich alles!' }],
            });
            setPhase('P5_LEARNING');
        } catch (error) {
            updateState({
                loading: false,
                llmOutput: `Fehler beim Generieren des Materials: ${error.message}`
            });
        }
    };

    const triggerRemediation = async () => {
        // P5.5 - Start Diagnose
        updateState({ loading: true, llmOutput: 'Lücken-Diagnose gestartet. Tutor wird kontaktiert...' });

        try {
            const result = await alisAPI.diagnoseLuecke(
                state.userId,
                state.goalId,
                state.pathStructure,
                state.currentConcept
            );

            updateState({
                loading: false,
                llmOutput: result.data.llm_output,
                remediationNeeded: true,
                tutorChat: [...state.tutorChat, { sender: 'Tutor', message: result.data.llm_output }],
            });
        } catch (error) {
            updateState({
                loading: false,
                llmOutput: `Fehler bei der Diagnose: ${error.message}`
            });
        }
        // Phase bleibt P5, aber der Chat-Input ändert sich zur Remediation-Antwort
    };

    const handleChatOrRemediationInput = async () => {
        if (!state.userInput) return;

        const userInput = state.userInput;
        updateState({ loading: true, userInput: '' });

        // Füge die Nutzer-Nachricht zum Chat hinzu
        const newChat = [...state.tutorChat, { sender: 'Nutzer', message: userInput }];
        updateState({ tutorChat: newChat, llmOutput: 'Antwort des Tutors/Architekten wird generiert...' });

        try {
            if (state.remediationNeeded) {
                // P5.5 - Remediation Execution
                const remediationResult = await alisAPI.performRemediation(
                    state.userId,
                    state.goalId,
                    userInput,
                    state.pathStructure,
                    state.currentConcept
                );

                // Führe sofort P4 für das neue Konzept (N1) aus
                const materialResult = await alisAPI.getMaterial(
                    state.userId,
                    state.goalId,
                    remediationResult.data.path_structure,
                    remediationResult.data.current_concept,
                    state.userProfile
                );

                updateState({
                    loading: false,
                    llmOutput: materialResult.data.llm_output,
                    pathStructure: remediationResult.data.path_structure,
                    currentConcept: remediationResult.data.current_concept,
                    remediationNeeded: false,
                    tutorChat: [
                        ...newChat,
                        {
                            sender: 'Architekt/System',
                            message: remediationResult.data.llm_output + " " + materialResult.data.llm_output.split('\n')[0]
                        }
                    ]
                });
                setPhase('P5_LEARNING');
            } else {
                // P5 - Standard Chat
                const chatResult = await alisAPI.chat(
                    state.userId,
                    state.goalId,
                    userInput,
                    state.currentConcept
                );

                updateState({
                    loading: false,
                    llmOutput: state.llmOutput, // Material bleibt sichtbar
                    tutorChat: [...newChat, { sender: 'Tutor', message: chatResult.data.llm_output }],
                });
            }
        } catch (error) {
            updateState({
                loading: false,
                tutorChat: [
                    ...newChat,
                    { sender: 'System', message: `Fehler: ${error.message}` }
                ]
            });
        }
    };

    const startTestGeneration = async () => {
        if (!state.currentConcept) {
            updateState({ llmOutput: 'Fehler: Kein aktives Konzept für Test-Generierung gefunden.' });
            return;
        }
        updateState({ loading: true, llmOutput: 'Test-Generierung läuft... Kurator wird kontaktiert...' });

        try {
            const result = await alisAPI.generateTest(
                state.userId,
                state.goalId,
                state.currentConcept,
                state.userProfile
            );

            updateState({
                loading: false,
                llmOutput: result.data.llm_output, // Die generierten Testfragen
            });
            setPhase('P6_TEST_PHASE'); // Neue Phase für die Testanzeige
        } catch (error) {
            updateState({
                loading: false,
                llmOutput: `Fehler beim Generieren der Tests: ${error.message}`
            });
        }
    };

    // ==============================================================================
    // 4. RENDERING DER PHASEN
    // ==============================================================================

    const renderLearningUI = () => (
        <div className="flex flex-col lg:flex-row h-full">
            {/* Linke Seite: Lernpfad und Material */}
            <div className="w-full lg:w-3/4 p-6 overflow-y-auto bg-white rounded-l-xl shadow-lg">
                <h2 className="text-xl font-bold mb-4 flex items-center text-indigo-700">
                    <BookOpen className="mr-2" /> Lernphase: {state.currentConcept?.name}
                </h2>

                {/* Material-Content-Box */}
                <div className="p-6 bg-gray-50 text-blue-600 border border-gray-200 rounded-xl shadow-inner min-h-[300px]">
                    {state.loading ? (
                        <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin text-indigo-500" /></div>
                    ) : (
                        <div className="prose max-w-none " dangerouslySetInnerHTML={{ __html: state.llmOutput.replace(/\n/g, '<br/>') }} />
                    )}
                </div>

                {/* Remediation Button */}
                <div className="mt-6 flex justify-between items-center">
                    <button
                        onClick={triggerRemediation}
                        className="flex items-center px-4 py-2 bg-red-100 text-red-700 border border-red-300 rounded-full hover:bg-red-200 transition duration-150 shadow-md">
                        <AlertTriangle className="w-4 h-4 mr-2" />
                        Fundament fehlt / Lücke melden (P5.5)
                    </button>
                    <button
                        onClick={startTestGeneration} // Geänderter onClick Handler
                        className="flex items-center px-4 py-2 bg-green-600 text-white rounded-full hover:bg-green-700 transition duration-150 shadow-md"
                        disabled={state.loading}
                    >
                        Konzept verstanden (P6 starten) <ArrowRight className="w-4 h-4 ml-2" />
                    </button>
                </div>
            </div>

            {/* Rechte Seite: Tutor Chat */}
            <div className="w-full lg:w-1/4 p-4 border-l border-gray-200 bg-gray-50 text-gray-700 rounded-r-xl flex flex-col">
                <h3 className="text-lg font-semibold mb-3 flex items-center text-gray-700">
                    <MessageCircle className="mr-2 w-5 h-5" /> Tutor Chat
                </h3>
                <div className="flex-grow overflow-y-auto space-y-3 p-2 bg-white rounded-lg shadow-inner mb-4">
                    {state.tutorChat.map((chat, index) => (
                        <div key={index} className={`max-w-[90%] p-2 rounded-lg text-sm ${chat.sender === 'Nutzer' ? 'ml-auto bg-indigo-100 text-indigo-800' : 'bg-gray-200 text-gray-800'}`}>
                            <strong>{chat.sender}:</strong> {chat.message}
                        </div>
                    ))}
                </div>

                {/* Chat Input */}
                <div className="flex items-center">
                    <input
                        type="text"
                        placeholder={state.remediationNeeded ? "Welches Fundament fehlt Ihnen? (P5.5)" : "Fragen Sie den Tutor..."}
                        value={state.userInput}
                        onChange={(e) => updateState({ userInput: e.target.value })}
                        onKeyPress={(e) => e.key === 'Enter' && handleChatOrRemediationInput()}
                        className="flex-grow p-3 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        disabled={state.loading}
                    />
                    <button
                        onClick={handleChatOrRemediationInput}
                        className="p-3 bg-indigo-600 text-white rounded-r-lg hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-400"
                        disabled={state.loading || !state.userInput}
                    >
                        {state.loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowRight className="w-5 h-5" />}
                    </button>
                </div>
                {state.remediationNeeded && <p className="text-xs text-red-500 mt-1">Geben Sie das fehlende Konzept ein, um den Pfad zu korrigieren.</p>}
            </div>
        </div>
    );

    const renderGoalSettingUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-xl mx-auto my-20">
            <h1 className="text-3xl font-extrabold text-indigo-700 mb-4 flex items-center">
                <Zap className="mr-3 w-7 h-7" /> ALIS: Ziel-Kontrakt (P1)
            </h1>
            <p className="text-gray-600 mb-6">
                Definieren Sie Ihr Lernziel. Der **Architekt** standardisiert es in einen messbaren **SMART-Vertrag**.
            </p>
            <textarea
                className="w-full p-4 border-2 border-indigo-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none min-h-[150px]"
                placeholder="Beispiel: Ich möchte Multi-Agenten-Systeme in der Logistik implementieren."
                value={goalInput}
                onChange={(e) => setGoalInput(e.target.value)}
            />
            <button
                onClick={startGoalSetting}
                className="w-full mt-4 flex items-center justify-center p-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-400"
                disabled={state.loading || !goalInput}
            >
                {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <Zap className="mr-2 w-5 h-5" />}
                {state.loading ? 'Ziel wird verhandelt...' : 'SMART-Vertrag erstellen'}
            </button>
            {!state.loading && state.llmOutput && phase !== 'P1_GOAL_SETTING' && (
                <div className="mt-4 p-4 text-sm bg-indigo-50 rounded-lg text-indigo-700 border border-indigo-200">
                    <p>Aktuelle LLM-Nachricht: {state.llmOutput.split('\n')[0]}...</p>
                </div>
            )}
        </div>
    );

    const renderPathReviewUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-3xl mx-auto my-10">
            <h1 className="text-3xl font-extrabold text-indigo-700 mb-6 flex items-center">
                <LayoutList className="mr-3 w-7 h-7" /> Lernpfad-Review (P3)
            </h1>
            <p className="text-gray-600 mb-6">
                Bitte prüfen Sie den vom **Architekten** generierten Plan. Markieren Sie Konzepte, die Ihnen bereits bekannt sind, um sie zu überspringen (Experten-Review).
            </p>

            <ul className="space-y-3 mb-8">
                {state.pathStructure.map((concept, index) => (
                    <li key={concept.id} className={`flex items-center justify-between p-4 rounded-lg transition duration-150 ${concept.status === 'Aktiv' ? 'bg-indigo-100 border-l-4 border-indigo-600 font-semibold' :
                        concept.status === 'Übersprungen' ? 'bg-green-50 line-through text-gray-500' :
                            'bg-gray-50 border border-gray-200 text-gray-500'
                        }`}>
                        <span className="flex items-center">
                            {index + 1}. {concept.name}
                            {concept.status === 'Übersprungen' && <span className="ml-2 text-xs font-bold text-green-700">(Übersprungen: {concept.expertiseSource})</span>}
                        </span>
                        <input
                            type="checkbox"
                            checked={concept.status === 'Übersprungen'}
                            onChange={() => {
                                // Simulation der Pfad-Änderung in der UI
                                const newPath = state.pathStructure.map(c =>
                                    c.id === concept.id ?
                                        { ...c, status: c.status === 'Übersprungen' ? 'Offen' : 'Übersprungen', expertiseSource: c.status === 'Übersprungen' ? null : 'P3 Experte' } : c
                                );
                                updateState({ pathStructure: newPath });
                            }}
                            className="h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                        />
                    </li>
                ))}
            </ul>

            <button
                onClick={confirmPathAndStartLearning}
                className="w-full flex items-center justify-center p-3 bg-green-600 text-white font-semibold rounded-lg shadow-lg hover:bg-green-700 transition duration-150"
            >
                {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <BookOpen className="mr-2 w-5 h-5" />}
                Lernpfad bestätigen & Material starten
            </button>
        </div>
    );

    const renderTestUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-3xl mx-auto my-10">
            <h1 className="text-3xl font-extrabold text-indigo-700 mb-6 flex items-center">
                <Zap className="mr-3 w-7 h-7" /> Test (P6)
            </h1>
            <p className="text-gray-600 mb-6">
                Der **Kurator** hat Testfragen für das Konzept "{state.currentConcept?.name}" generiert.
            </p>
            <div className="p-6 bg-gray-50 text-blue-600 border border-gray-200 rounded-xl shadow-inner min-h-[300px]">
                {state.loading ? (
                    <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin text-indigo-500" /></div>
                ) : (
                    <div className="prose max-w-none " dangerouslySetInnerHTML={{ __html: state.llmOutput.replace(/\n/g, '<br/>') }} />
                )}
            </div>
            {/* Hier könnten später Eingabefelder für Antworten und ein "Test abschließen" Button folgen */}
            <button
                onClick={() => { /* Logik für Test abschicken/bewerten */ alert('Test abschicken (Funktionalität noch nicht implementiert)'); }}
                className="w-full mt-6 flex items-center justify-center p-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150"
            >
                Test abschließen & bewerten
            </button>
        </div>
    );

    // ==============================================================================
    // 5. HAUPT-LAYOUT UND SWITCH
    // ==============================================================================

    return (
        <div className="min-h-screen bg-gray-100 font-sans p-4">
            {phase === 'P1_GOAL_SETTING' && renderGoalSettingUI()}
            {phase === 'P3_PATH_REVIEW' && renderPathReviewUI()}
            {phase === 'P5_LEARNING' && renderLearningUI()}
            {phase === 'P6_TEST_PHASE' && renderTestUI()}
        </div>
    );
};

export default App;