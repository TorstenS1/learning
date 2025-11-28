import React, { useState, useEffect } from 'react';
import { Loader2, Zap, LayoutList, BookOpen, MessageCircle, AlertTriangle, ArrowRight, CheckCircle, XCircle, BrainCircuit } from 'lucide-react';
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
    const [pretest, setPretest] = useState(true);
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
        parsedTestQuestions: [], // New state to store parsed test questions
        userTestAnswers: {},    // New state to store user's answers
        testEvaluationResult: null, // New state for evaluation results
    });

    const updateState = (updates) => setState(s => ({ ...s, ...updates }));

    // Prevent accidental browser back navigation during learning session
    useEffect(() => {
        const handlePopState = (e) => {
            e.preventDefault();
            const confirmLeave = window.confirm(
                'Möchten Sie wirklich die Lernumgebung verlassen? Ihr Fortschritt könnte verloren gehen.'
            );
            if (!confirmLeave) {
                window.history.pushState(null, '', window.location.href);
            }
        };

        // Push initial state
        window.history.pushState(null, '', window.location.href);
        window.addEventListener('popstate', handlePopState);

        return () => {
            window.removeEventListener('popstate', handlePopState);
        };
    }, []);

    // Debug Render Cycle
    console.log('--- RENDER CYCLE ---');
    console.log('Current Phase:', phase);
    console.log('Loading:', state.loading);
    console.log('Test Result:', state.testEvaluationResult);

    // Helper to parse LLM output for test questions
    useEffect(() => {
        if ((phase === 'P6_TEST_PHASE' || phase === 'P2_PRIOR_KNOWLEDGE') && state.llmOutput) {
            console.log("Parsing questions for phase:", phase);
            console.log("LLM Output to parse:", state.llmOutput);
            try {
                // Assuming llmOutput is a JSON string with a 'test_questions' key
                const parsed = JSON.parse(state.llmOutput);
                console.log("Parsed JSON:", parsed);

                // Handle P2 format (questions array directly or inside 'questions' key) vs P6 format (test_questions)
                let questions = [];
                if (parsed.test_questions && Array.isArray(parsed.test_questions)) {
                    questions = parsed.test_questions;
                } else if (parsed.questions && Array.isArray(parsed.questions)) {
                    questions = parsed.questions;
                }

                if (questions.length > 0) {
                    console.log("Found questions:", questions);
                    updateState({ parsedTestQuestions: questions });
                    // Initialize userTestAnswers
                    const initialAnswers = {};
                    questions.forEach((q, index) => {
                        initialAnswers[q.id || `q${index}`] = q.type === 'multiple_choice' ? '' : '';
                    });
                    updateState({ userTestAnswers: initialAnswers });
                } else {
                    console.warn("LLM output did not contain valid questions array:", parsed);
                    updateState({ parsedTestQuestions: [] });
                }
            } catch (e) {
                console.error("Error parsing test questions LLM output:", e);
                updateState({ parsedTestQuestions: [] });
            }
        } else if (phase !== 'P6_TEST_PHASE' && phase !== 'P2_PRIOR_KNOWLEDGE' && !phase.startsWith('P7_')) {
            // Clear test-related states when leaving P6 or P2 (but keep them for P7 evaluation display)
            if (state.parsedTestQuestions.length > 0 || Object.keys(state.userTestAnswers).length > 0) {
                // Don't clear testEvaluationResult here, as it might be needed for P7
                updateState({ parsedTestQuestions: [], userTestAnswers: {} });
            }
        }
    }, [phase, state.llmOutput]);

    // Handle user input for test questions
    const handleAnswerChange = (questionId, value) => {
        // Correctly construct the new userTestAnswers object and pass it to updateState
        const newAnswers = {
            ...state.userTestAnswers,
            [questionId]: value,
        };
        updateState({ userTestAnswers: newAnswers });
    };

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

            const goalData = {
                goalId: result.data.goalId || 'G-TEMP-001',
                llmOutput: result.data.llm_output,
                pathStructure: result.data.path_structure,
                currentConcept: result.data.current_concept,
            };

            // Update state with the goal data
            updateState({
                loading: false, // Will be set to true again by startPriorKnowledgeTest if pretest is true
                ...goalData
            });

            // Decide next phase based on 'pretest' setting
            if (pretest) {
                // Directly initiate prior knowledge test
                await startPriorKnowledgeTest(goalData.goalId, goalData.pathStructure);
            } else {
                // Go directly to the path review, skipping the choice screen
                setPhase('P3_PATH_REVIEW');
            }
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
        // Don't set phase here - wait for API response

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

    const submitTest = async () => {
        if (!state.currentConcept || !state.parsedTestQuestions.length) {
            updateState({ llmOutput: 'Fehler: Keine Testfragen oder kein aktives Konzept zum Bewerten vorhanden.' });
            return;
        }
        updateState({ loading: true, llmOutput: '{ "test_questions": ' + JSON.stringify(state.parsedTestQuestions) + ' }' });

        try {
            const result = await alisAPI.submitTest(
                state.userId,
                state.goalId,
                state.currentConcept,
                state.parsedTestQuestions, // Original questions sent for context
                state.userTestAnswers,
                state.pathStructure // Pass current path structure so backend can return it
            );

            updateState({
                loading: false,
                llmOutput: result.data.llm_output, // LLM's evaluation output
                testEvaluationResult: result.data.evaluation_result, // Structured evaluation
                pathStructure: result.data.path_structure, // Updated path with concept status
                currentConcept: result.data.current_concept, // May be updated if moving to next concept
            });

            // P7 Adaption Logic: Decide next phase based on evaluation result
            // Use result.data values directly to avoid race condition with state updates
            console.log('Test evaluation result:', result.data.evaluation_result);
            console.log('Path structure:', result.data.path_structure);
            console.log('Current concept:', result.data.current_concept);

            if (result.data.evaluation_result?.passed) {
                // Check if there's a next concept in the path
                const updatedPathStructure = result.data.path_structure;
                const updatedCurrentConcept = result.data.current_concept;
                const currentIndex = updatedPathStructure.findIndex(c => c.id === updatedCurrentConcept.id);
                const hasNextConcept = currentIndex !== -1 && currentIndex + 1 < updatedPathStructure.length;

                console.log('Test passed! Current index:', currentIndex, 'Has next concept:', hasNextConcept);

                if (hasNextConcept) {
                    // Move to next concept - show transition UI
                    console.log('Transitioning to P7_PROGRESSION');
                    setPhase('P7_PROGRESSION');
                } else {
                    // Goal complete!
                    console.log('Transitioning to P7_GOAL_COMPLETE');
                    setPhase('P7_GOAL_COMPLETE');
                }
            } else {
                // Test failed - show remediation options
                console.log('Test failed! Transitioning to P7_REMEDIATION_CHOICE');
                setPhase('P7_REMEDIATION_CHOICE');
            }
        } catch (error) {
            updateState({
                loading: false,
                llmOutput: `Fehler beim Bewerten des Tests: ${error.message}`
            });
        }
    };

    const startPriorKnowledgeTest = async (goalIdFromParam, pathStructureFromParam) => {
        const goalIdToUse = goalIdFromParam || state.goalId;
        const pathStructureToUse = pathStructureFromParam || state.pathStructure;

        console.log("Starting P2 test generation...");
        updateState({ loading: true, llmOutput: 'Prüfer generiert Vorwissenstest...' });
        try {
            const result = await alisAPI.generatePriorKnowledgeTest(
                state.userId,
                goalIdToUse,
                pathStructureToUse
            );
            console.log("P2 API Result:", result);
            updateState({
                loading: false,
                llmOutput: result.llm_output // Contains test questions JSON
            });
            console.log("Setting phase to P2_PRIOR_KNOWLEDGE");
            setPhase('P2_PRIOR_KNOWLEDGE');
        } catch (error) {
            console.error("Error in startPriorKnowledgeTest:", error);
            updateState({ loading: false, llmOutput: 'Fehler bei P2 Generierung' });
        }
    };

    const submitPriorKnowledgeTest = async () => {
        updateState({ loading: true, llmOutput: 'Prüfer bewertet Vorwissen...' });
        try {
            const result = await alisAPI.evaluatePriorKnowledgeTest(
                state.userId,
                state.goalId,
                state.pathStructure,
                state.parsedTestQuestions,
                state.userTestAnswers
            );
            updateState({
                loading: false,
                llmOutput: result.llm_output, // Feedback
                pathStructure: result.path_structure // Updated with skipped concepts
            });
            setPhase('P3_PATH_REVIEW');
        } catch (error) {
            console.error(error);
            updateState({ loading: false, llmOutput: 'Fehler bei P2 Bewertung' });
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
                        className="flex-grow p-3 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900 bg-white"
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
                className="w-full p-4 border-2 border-indigo-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none min-h-[150px] text-gray-900 bg-white"
                placeholder="Beispiel: Ich möchte Multi-Agenten-Systeme in der Logistik implementieren."
                value={goalInput}
                onChange={(e) => setGoalInput(e.target.value)}
            />
            <div className="mt-4 flex items-center justify-center">
                <input
                    type="checkbox"
                    id="pretest-toggle"
                    checked={pretest}
                    onChange={(e) => setPretest(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <label htmlFor="pretest-toggle" className="ml-2 block text-sm text-gray-700">
                    Vorwissenstest zu Beginn durchführen
                </label>
            </div>
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

    const renderPriorKnowledgeTestUI = () => {
        console.log("Rendering P2 UI. Questions:", state.parsedTestQuestions);
        return (
            <div className="p-8 bg-white rounded-xl shadow-2xl max-w-3xl mx-auto my-10">
                <h1 className="text-3xl font-extrabold text-indigo-700 mb-6 flex items-center">
                    <BrainCircuit className="mr-3 w-7 h-7" /> Vorwissenstest (P2)
                </h1>
                <p className="text-gray-600 mb-6">
                    Bitte beantworten Sie die folgenden Fragen, damit wir Ihren Lernpfad anpassen können.
                </p>

                <div className="space-y-6">
                    {state.parsedTestQuestions.map((question, index) => (
                        <div key={question.id || index} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                            <p className="font-semibold text-lg mb-3 text-gray-800">
                                {index + 1}. {question.question_text}
                            </p>
                            {question.type === 'multiple_choice' ? (
                                <div className="space-y-2">
                                    {question.options.map((option, optIndex) => (
                                        <label key={optIndex} className="flex items-center space-x-3 cursor-pointer p-2 hover:bg-gray-100 rounded">
                                            <input
                                                type="radio"
                                                name={question.id}
                                                value={option}
                                                checked={state.userTestAnswers[question.id] === option}
                                                onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                                                className="form-radio h-5 w-5 text-indigo-600"
                                            />
                                            <span className="text-gray-700">{option}</span>
                                        </label>
                                    ))}
                                </div>
                            ) : (
                                <textarea
                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 bg-white"
                                    rows="3"
                                    placeholder="Ihre Antwort..."
                                    value={state.userTestAnswers[question.id] || ''}
                                    onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                                />
                            )}
                        </div>
                    ))}
                </div>

                <button
                    onClick={submitPriorKnowledgeTest}
                    className="w-full mt-8 flex items-center justify-center p-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-400"
                    disabled={state.loading}
                >
                    {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <CheckCircle className="mr-2 w-5 h-5" />}
                    Test einreichen & Pfad anpassen
                </button>
            </div>
        );
    };

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

    const renderTestUI = () => {
        // console.log("renderTestUI: state.loading is", state.loading); // Removed DEBUG LOG
        console.log("renderTestUI: state.userTestAnswers", state.userTestAnswers); // DEBUG LOG
        console.log("renderTestUI: state.parsedTestQuestions", state.parsedTestQuestions); // DEBUG LOG
        return (
            <div className="p-8 bg-white rounded-xl shadow-2xl max_w-3xl mx-auto my-10">
                <h1 className="text-3xl font-extrabold text-indigo-700 mb-6 flex items-center">
                    <Zap className="mr-3 w-7 h-7" /> Test (P6)
                </h1>
                <p className="text-gray-600 mb-6">
                    Der **Kurator** hat Testfragen für das Konzept "{state.currentConcept?.name}" generiert. Bitte beantworten Sie die Fragen:
                </p>
                {state.parsedTestQuestions.length > 0 ? (
                    <div className="space-y-6">
                        {state.parsedTestQuestions.map((q, qIndex) => (
                            <div key={q.id || `q${qIndex}`} className="p-4 bg-gray-50 text-gray-700 border border-gray-200 rounded-lg">
                                <p className="font-semibold text-gray-800 mb-2">{qIndex + 1}. {q.question_text}</p>
                                {q.type === 'multiple_choice' ? (
                                    <div className="space-y-2 ml-4">
                                        {q.options && q.options.map((option, oIndex) => (
                                            <label key={oIndex} className="flex items-center">
                                                <input
                                                    type="radio"
                                                    name={`question - ${q.id || `q${qIndex}`}`}
                                                    value={option}
                                                    checked={state.userTestAnswers[q.id || `q${qIndex}`] === option}
                                                    onChange={(e) => handleAnswerChange(q.id || `q${qIndex}`, e.target.value)}
                                                    className="form-radio text-indigo-600 h-4 w-4"
                                                />
                                                <span className="ml-2">{option}</span>
                                            </label>
                                        ))}
                                    </div>
                                ) : ( // Default to free_text
                                    <textarea
                                        className="w-full p-3 mt-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y min-h-[80px] text-gray-900 bg-white"
                                        placeholder="Ihre Antwort..."
                                        value={state.userTestAnswers[q.id || `q${qIndex}`] || ''}
                                        onChange={(e) => handleAnswerChange(q.id || `q${qIndex}`, e.target.value)}
                                    />)}
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-red-500">Es konnten keine Testfragen geladen werden oder das Format ist ungültig.</p>
                )}

                <button
                    onClick={submitTest}
                    className="w-full mt-6 flex items-center justify-center p-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-400"
                    disabled={state.loading}
                >                        {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <CheckCircle className="mr-2 w-5 h-5" />}
                    Test abschließen & bewerten
                </button>
            </div>
        );
    };

    // ==============================================================================
    // P7: ADAPTION & PROGRESSION UIs
    // ==============================================================================

    const renderQuestionResults = () => {
        if (!state.testEvaluationResult?.question_results?.length) return null;

        return (
            <div className="mt-8 text-left">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Detaillierte Auswertung:</h3>
                <div className="space-y-4">
                    {state.testEvaluationResult.question_results.map((result, index) => (
                        <div key={index} className={`p-4 rounded-lg border ${result.is_correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                            <div className="flex items-start">
                                <div className="flex-shrink-0 mt-1">
                                    {result.is_correct ? <CheckCircle className="w-5 h-5 text-green-600" /> : <XCircle className="w-5 h-5 text-red-600" />}
                                </div>
                                <div className="ml-3">
                                    <p className="font-semibold text-gray-900">{result.question_text}</p>
                                    <p className="text-sm mt-1">
                                        <span className="font-medium">Ihre Antwort:</span> {result.user_answer}
                                    </p>
                                    {!result.is_correct && (
                                        <p className="text-sm mt-1 text-green-700">
                                            <span className="font-medium">Richtige Antwort:</span> {result.correct_answer}
                                        </p>
                                    )}
                                    <p className="text-sm mt-2 text-gray-600 italic">
                                        {result.explanation}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const renderProgressionUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-2xl mx-auto my-20">
            <div className="text-center">
                <CheckCircle className="w-20 h-20 text-green-600 mx-auto mb-4" />
                <h1 className="text-3xl font-extrabold text-green-700 mb-4">
                    🎉 Glückwunsch! Test bestanden!
                </h1>
                <p className="text-gray-600 mb-6">
                    Sie haben das Konzept <strong>"{state.currentConcept?.name}"</strong> erfolgreich gemeistert.
                </p>

                {state.testEvaluationResult && (
                    <div className="bg-green-50 p-4 rounded-lg mb-6">
                        <p className="text-lg font-semibold">Score: {state.testEvaluationResult.score}%</p>
                        <p className="text-gray-700 mt-2">{state.testEvaluationResult.feedback}</p>
                    </div>
                )}

                {renderQuestionResults()}

                <button
                    onClick={async () => {
                        // Move to next concept
                        const currentIndex = state.pathStructure.findIndex(c => c.id === state.currentConcept.id);
                        const nextConcept = state.pathStructure[currentIndex + 1];

                        updateState({
                            currentConcept: nextConcept,
                            loading: true,
                            llmOutput: 'Kurator generiert Material für das nächste Konzept...'
                        });

                        try {
                            const result = await alisAPI.getMaterial(
                                state.userId,
                                state.goalId,
                                state.pathStructure,
                                nextConcept,
                                state.userProfile
                            );

                            updateState({
                                loading: false,
                                llmOutput: result.data.llm_output,
                                tutorChat: [{ sender: 'System', message: `Willkommen beim Konzept: ${nextConcept.name}!` }],
                            });
                            setPhase('P5_LEARNING');
                        } catch (error) {
                            updateState({
                                loading: false,
                                llmOutput: `Fehler: ${error.message}`
                            });
                        }
                    }}
                    className="w-full flex items-center justify-center p-4 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150"
                    disabled={state.loading}
                >
                    {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <ArrowRight className="mr-2 w-5 h-5" />}
                    Weiter zum nächsten Konzept
                </button>
            </div>
        </div>
    );

    const renderGoalCompleteUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-2xl mx-auto my-20">
            <div className="text-center">
                <CheckCircle className="w-24 h-24 text-green-600 mx-auto mb-6 animate-bounce" />
                <h1 className="text-4xl font-extrabold text-green-700 mb-4">
                    🏆 Lernziel erreicht!
                </h1>
                <p className="text-xl text-gray-600 mb-6">
                    Herzlichen Glückwunsch! Sie haben alle Konzepte erfolgreich abgeschlossen.
                </p>

                {state.testEvaluationResult && (
                    <div className="bg-green-50 p-6 rounded-lg mb-6">
                        <p className="text-lg font-semibold mb-2">Letzter Test:</p>
                        <p className="text-2xl font-bold text-green-700">{state.testEvaluationResult.score}%</p>
                        <p className="text-gray-700 mt-2">{state.testEvaluationResult.feedback}</p>
                    </div>
                )}

                {renderQuestionResults()}

                <div className="space-y-3">
                    <button
                        onClick={() => {
                            setPhase('P1_GOAL_SETTING');
                            setGoalInput('');
                            updateState({
                                goalId: null,
                                pathStructure: [],
                                currentConcept: null,
                                llmOutput: "Definieren Sie Ihr Lernziel, um den Architekten zu starten.",
                                tutorChat: [],
                                testEvaluationResult: null
                            });
                        }}
                        className="w-full flex items-center justify-center p-4 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150"
                    >
                        <Zap className="mr-2 w-5 h-5" />
                        Neues Lernziel starten
                    </button>
                </div>
            </div>
        </div>
    );

    const renderRemediationChoiceUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-2xl mx-auto my-20">
            <div className="text-center">
                <XCircle className="w-20 h-20 text-red-600 mx-auto mb-4" />
                <h1 className="text-3xl font-extrabold text-red-700 mb-4">
                    Test nicht bestanden
                </h1>
                <p className="text-gray-600 mb-6">
                    Keine Sorge! Lernen ist ein Prozess. Wählen Sie, wie Sie fortfahren möchten:
                </p>

                {state.testEvaluationResult && (
                    <div className="bg-red-50 p-4 rounded-lg mb-6">
                        <p className="text-lg font-semibold">Score: {state.testEvaluationResult.score}%</p>
                        <p className="text-gray-700 mt-2">{state.testEvaluationResult.feedback}</p>
                        {state.testEvaluationResult.recommendation && (
                            <p className="text-gray-800 mt-2 font-semibold">
                                💡 Empfehlung: {state.testEvaluationResult.recommendation}
                            </p>
                        )}
                    </div>
                )}

                {renderQuestionResults()}

                <div className="space-y-3">
                    <button
                        onClick={async () => {
                            // Re-study current concept
                            updateState({ loading: true, llmOutput: 'Material wird neu geladen...' });

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
                                    tutorChat: [{ sender: 'System', message: 'Lassen Sie uns das Konzept noch einmal durchgehen!' }],
                                    testEvaluationResult: null
                                });
                                setPhase('P5_LEARNING');
                            } catch (error) {
                                updateState({
                                    loading: false,
                                    llmOutput: `Fehler: ${error.message}`
                                });
                            }
                        }}
                        className="w-full flex items-center justify-center p-4 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150"
                        disabled={state.loading}
                    >
                        {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <BookOpen className="mr-2 w-5 h-5" />}
                        Konzept wiederholen
                    </button>

                    <button
                        onClick={() => {
                            setPhase('P5_LEARNING');
                            updateState({
                                remediationNeeded: true,
                                testEvaluationResult: null,
                                tutorChat: [...state.tutorChat, {
                                    sender: 'System',
                                    message: 'Nutzen Sie den "Fundament fehlt"-Button, um fehlende Grundlagen zu identifizieren.'
                                }]
                            });
                        }}
                        className="w-full flex items-center justify-center p-4 bg-yellow-600 text-white font-semibold rounded-lg shadow-lg hover:bg-yellow-700 transition duration-150"
                    >
                        <AlertTriangle className="mr-2 w-5 h-5" />
                        Grundlagen-Lücke melden (P5.5)
                    </button>
                </div>
            </div>
        </div>
    );

    // ==============================================================================
    // 5. HAUPT-LAYOUT UND SWITCH
    // ==============================================================================

    return (
        <div className="min-h-screen bg-gray-100 font-sans p-4">
            {phase === 'P1_GOAL_SETTING' && renderGoalSettingUI()}
            {phase === 'P2_PRIOR_KNOWLEDGE' && renderPriorKnowledgeTestUI()}
            {phase === 'P3_PATH_REVIEW' && renderPathReviewUI()}
            {phase === 'P5_LEARNING' && renderLearningUI()}
            {phase === 'P6_TEST_PHASE' && renderTestUI()}
            {phase === 'P7_PROGRESSION' && renderProgressionUI()}
            {phase === 'P7_GOAL_COMPLETE' && renderGoalCompleteUI()}
            {phase === 'P7_REMEDIATION_CHOICE' && renderRemediationChoiceUI()}
        </div>
    );
};



export default App;