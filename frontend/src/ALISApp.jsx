import React, { useState, useEffect } from 'react';
import { Loader2, Zap, LayoutList, BookOpen, MessageCircle, AlertTriangle, ArrowRight, CheckCircle, XCircle, BrainCircuit } from 'lucide-react';
import alisAPI from './services/alisAPI';
import { getTranslations, getStoredLanguage } from './i18n';

// ==============================================================================
// 2. MAIN COMPONENT
// ==============================================================================

const App = () => {
    const [phase, setPhase] = useState('P1_GOAL_SETTING');
    const [goalInput, setGoalInput] = useState('');
    const [pretest, setPretest] = useState(true);
    const [language, setLanguage] = useState(getStoredLanguage());
    const t = getTranslations(language);

    const [state, setState] = useState({
        userId: 'ALIS-User-ID-12345',
        goalId: null,
        pathStructure: [],
        currentConcept: null,
        llmOutput: "Define your learning goal to start the Architect.",
        userInput: '',
        remediationNeeded: false,
        userProfile: { stylePreference: 'Analogy-based', paceWPM: 180 },
        loading: false,
        tutorChat: [],
        parsedTestQuestions: [],
        userTestAnswers: {},
        testEvaluationResult: null,
    });

    const updateState = (updates) => setState(s => ({ ...s, ...updates }));

    const changeLanguage = (lang) => {
        setLanguage(lang);
        localStorage.setItem('alis_language', lang);
    };


    useEffect(() => {
        const handlePopState = (e) => {
            e.preventDefault();
            const confirmLeave = window.confirm(
                'Do you really want to leave the learning environment? Your progress might be lost.'
            );
            if (!confirmLeave) {
                window.history.pushState(null, '', window.location.href);
            }
        };

        window.history.pushState(null, '', window.location.href);
        window.addEventListener('popstate', handlePopState);

        return () => {
            window.removeEventListener('popstate', handlePopState);
        };
    }, []);

    console.log('--- RENDER CYCLE ---');
    console.log('Current Phase:', phase);
    console.log('Loading:', state.loading);
    console.log('Test Result:', state.testEvaluationResult);

    useEffect(() => {
        if ((phase === 'P6_TEST_PHASE' || phase === 'P2_PRIOR_KNOWLEDGE') && state.llmOutput) {
            try {
                // Only attempt to parse if it looks like JSON
                if (typeof state.llmOutput === 'string' && state.llmOutput.trim().startsWith('{')) {
                    const parsed = JSON.parse(state.llmOutput);
                    let questions = parsed.test_questions || parsed.questions || [];

                    if (questions.length > 0) {
                        updateState({ parsedTestQuestions: questions });
                        const initialAnswers = {};
                        questions.forEach((q, index) => {
                            initialAnswers[q.id || `q${index}`] = q.type === 'multiple_choice' ? '' : '';
                        });
                        updateState({ userTestAnswers: initialAnswers });
                    } else {
                        updateState({ parsedTestQuestions: [] });
                    }
                }
            } catch (e) {
                console.error("Error parsing test questions LLM output:", e);
                updateState({ parsedTestQuestions: [] });
            }
        } else if (phase !== 'P6_TEST_PHASE' && phase !== 'P2_PRIOR_KNOWLEDGE' && !phase.startsWith('P7_')) {
            if (state.parsedTestQuestions.length > 0 || Object.keys(state.userTestAnswers).length > 0) {
                updateState({ parsedTestQuestions: [], userTestAnswers: {} });
            }
        }
    }, [phase, state.llmOutput]);

    const handleAnswerChange = (questionId, value) => {
        updateState({ userTestAnswers: { ...state.userTestAnswers, [questionId]: value } });
    };

    // ==============================================================================
    // 3. WORKFLOW FUNCTIONS
    // ==============================================================================

    const startGoalSetting = async () => {
        if (!goalInput) return;
        updateState({ loading: true, llmOutput: 'Contacting Architect...' });

        try {
            const result = await alisAPI.startGoal(state.userId, goalInput, state.userProfile, language);
            const goalData = {
                goalId: result.data.goalId || 'G-TEMP-001',
                llmOutput: result.data.llm_output,
                pathStructure: result.data.path_structure,
                currentConcept: result.data.current_concept,
            };
            updateState({ loading: false, ...goalData });

            if (pretest) {
                await startPriorKnowledgeTest(goalData.goalId, goalData.pathStructure);
            } else {
                setPhase('P3_PATH_REVIEW');
            }
        } catch (error) {
            updateState({ loading: false, llmOutput: `Error contacting Architect: ${error.message}` });
        }
    };

    const confirmPathAndStartLearning = async () => {
        // Find first open concept
        console.log("Path Structure:", state.pathStructure);
        const firstOpenConcept = state.pathStructure.find(c => c.status === 'Open' || c.status === 'Reactivated');
        console.log("First Open Concept:", firstOpenConcept);

        if (!firstOpenConcept) {
            updateState({ llmOutput: t.p7.goalComplete.description });
            setPhase('P7_GOAL_COMPLETE');
            return;
        }

        updateState({ loading: true, llmOutput: 'Contacting Curator...' });
        try {
            const result = await alisAPI.getMaterial(state.userId, state.goalId, state.pathStructure, firstOpenConcept, state.userProfile);

            updateState({
                loading: false,
                llmOutput: result.data.llm_output,
                currentConcept: result.data.current_concept
            });

            if (result.data.current_concept) {
                setPhase('P5_LEARNING');
            } else {
                setPhase('P7_GOAL_COMPLETE');
            }
        } catch (error) {
            updateState({ loading: false, llmOutput: `Error fetching material: ${error.message}` });
        }
    };

    const triggerRemediation = async () => {
        updateState({ loading: true, llmOutput: 'Starting gap diagnosis. Contacting Tutor...' });
        try {
            const result = await alisAPI.diagnoseLuecke(state.userId, state.goalId, state.pathStructure, state.currentConcept);
            updateState({
                loading: false,
                llmOutput: result.data.llm_output,
                remediationNeeded: true,
                tutorChat: [...state.tutorChat, { sender: 'Tutor', message: result.data.llm_output }],
            });
        } catch (error) {
            updateState({ loading: false, llmOutput: `Error during diagnosis: ${error.message}` });
        }
    };

    const handleChatOrRemediationInput = async () => {
        if (!state.userInput) return;
        const userInput = state.userInput;
        updateState({ loading: true, userInput: '' });

        const newChat = [...state.tutorChat, { sender: 'User', message: userInput }];
        updateState({ tutorChat: newChat, llmOutput: 'Tutor/Architect is generating a response...' });

        try {
            if (state.remediationNeeded) {
                const remediationResult = await alisAPI.performRemediation(state.userId, state.goalId, userInput, state.pathStructure, state.currentConcept);
                const materialResult = await alisAPI.getMaterial(state.userId, state.goalId, remediationResult.data.path_structure, remediationResult.data.current_concept, state.userProfile);
                updateState({
                    loading: false,
                    llmOutput: materialResult.data.llm_output,
                    pathStructure: remediationResult.data.path_structure,
                    currentConcept: remediationResult.data.current_concept,
                    remediationNeeded: false,
                    tutorChat: [...newChat, { sender: 'Architect/System', message: remediationResult.data.llm_output + " " + materialResult.data.llm_output.split('\n')[0] }],
                });
                setPhase('P5_LEARNING');
            } else {
                const chatResult = await alisAPI.chat(state.userId, state.goalId, userInput, state.currentConcept);
                updateState({
                    loading: false,
                    llmOutput: state.llmOutput,
                    tutorChat: [...newChat, { sender: 'Tutor', message: chatResult.data.llm_output }],
                });
            }
        } catch (error) {
            updateState({ loading: false, tutorChat: [...newChat, { sender: 'System', message: `Error: ${error.message}` }] });
        }
    };

    const startTestGeneration = async () => {
        if (!state.currentConcept) {
            updateState({ llmOutput: 'Error: No active concept found for test generation.' });
            return;
        }
        updateState({ loading: true, llmOutput: 'Generating test... Contacting Curator...' });
        try {
            const result = await alisAPI.generateTest(state.userId, state.goalId, state.currentConcept, state.userProfile);
            updateState({ loading: false, llmOutput: result.data.llm_output });
            setPhase('P6_TEST_PHASE');
        } catch (error) {
            updateState({ loading: false, llmOutput: `Error generating test: ${error.message}` });
        }
    };

    const submitTest = async () => {
        if (!state.currentConcept || !state.parsedTestQuestions.length) {
            updateState({ llmOutput: 'Error: No test questions or active concept to evaluate.' });
            return;
        }
        updateState({ loading: true, llmOutput: `{ "test_questions": ${JSON.stringify(state.parsedTestQuestions)} }` });
        try {
            console.log('🚀 Submitting test...');
            const result = await alisAPI.submitTest(state.userId, state.goalId, state.currentConcept, state.parsedTestQuestions, state.userTestAnswers, state.pathStructure);
            console.log('✅ Test result received:', result);

            updateState({
                loading: false,
                llmOutput: result.data.llm_output,
                testEvaluationResult: result.data.evaluation_result, // Use the modified result
                pathStructure: result.data.path_structure,
                currentConcept: result.data.current_concept,
            });

            const passed = result.data.evaluation_result?.passed;
            console.log('🤔 Test passed?', passed);
            console.log('🤔 Next concept?', result.data.current_concept);

            if (passed) {
                if (result.data.current_concept) {
                    console.log('➡️ Transitioning to P7_PROGRESSION');
                    setPhase('P7_PROGRESSION');
                } else {
                    console.log('➡️ Transitioning to P7_GOAL_COMPLETE');
                    setPhase('P7_GOAL_COMPLETE');
                }
            } else {
                console.log('➡️ Transitioning to P7_REMEDIATION_CHOICE');
                setPhase('P7_REMEDIATION_CHOICE');
            }
        } catch (error) {
            console.error('❌ Error evaluating test:', error);
            updateState({ loading: false, llmOutput: `Error evaluating test: ${error.message}` });
        }
    };

    const startPriorKnowledgeTest = async (goalIdFromParam, pathStructureFromParam) => {
        const goalIdToUse = goalIdFromParam || state.goalId;
        const pathStructureToUse = pathStructureFromParam || state.pathStructure;
        updateState({ loading: true, llmOutput: t.p2.generating });
        try {
            const result = await alisAPI.generatePriorKnowledgeTest(state.userId, goalIdToUse, pathStructureToUse);
            updateState({ loading: false, llmOutput: result.llm_output });
            setPhase('P2_PRIOR_KNOWLEDGE');
        } catch (error) {
            updateState({ loading: false, llmOutput: t.common.error });
        }
    };

    const submitPriorKnowledgeTest = async () => {
        updateState({ loading: true, llmOutput: t.p2.evaluating });
        try {
            const result = await alisAPI.evaluatePriorKnowledgeTest(state.userId, state.goalId, state.pathStructure, state.parsedTestQuestions, state.userTestAnswers);
            updateState({
                loading: false,
                llmOutput: result.llm_output,
                pathStructure: result.path_structure,
                parsedTestQuestions: [],
                userTestAnswers: {},
            });
            setPhase('P3_PATH_REVIEW');
        } catch (error) {
            updateState({ loading: false, llmOutput: t.common.error });
        }
    };

    // ==============================================================================
    // SESSION MANAGEMENT
    // ==============================================================================

    const autoSaveSession = async () => {
        if (!state.goalId) return; // Only save if goal exists

        try {
            // Auto-generate session name from first concept or goal ID
            const autoSessionName = state.pathStructure?.[0]?.name || state.goalId || 'Auto-saved Session';

            await alisAPI.saveSession(state.userId, {
                phase,
                goalId: state.goalId,
                goalName: autoSessionName,
                pathStructure: state.pathStructure,
                currentConcept: state.currentConcept,
                llmOutput: state.llmOutput,
                tutorChat: state.tutorChat,
                testEvaluationResult: state.testEvaluationResult,
                parsedTestQuestions: state.parsedTestQuestions,
                userTestAnswers: state.userTestAnswers,
                remediationNeeded: state.remediationNeeded,
                language
            }, autoSessionName);
            console.log('✅ Session auto-saved:', autoSessionName);
        } catch (error) {
            console.error('❌ Auto-save failed:', error);
        }
    };

    const handleSaveSession = async () => {
        if (!state.goalId) {
            alert(t.session?.noGoal || 'Please create a learning goal first');
            return;
        }

        // Prompt for session name
        const goalName = state.pathStructure?.[0]?.name || state.goalId;
        const sessionName = prompt(
            t.session?.savePrompt || 'Enter a name for this session:',
            goalName
        );

        if (sessionName === null) return; // User cancelled

        updateState({ loading: true });
        try {
            await alisAPI.saveSession(state.userId, {
                phase,
                goalId: state.goalId,
                goalName: sessionName,
                pathStructure: state.pathStructure,
                currentConcept: state.currentConcept,
                llmOutput: state.llmOutput,
                tutorChat: state.tutorChat,
                testEvaluationResult: state.testEvaluationResult,
                parsedTestQuestions: state.parsedTestQuestions,
                userTestAnswers: state.userTestAnswers,
                remediationNeeded: state.remediationNeeded,
                language
            }, sessionName);
            updateState({ loading: false });
            alert(t.session?.saved || 'Progress saved successfully! ✅');
        } catch (error) {
            updateState({ loading: false });
            alert(t.session?.saveFailed || 'Failed to save progress');
        }
    };

    const handleLoadSession = async () => {
        updateState({ loading: true });
        try {
            // Get list of sessions
            console.log('🔍 Fetching sessions for user:', state.userId);
            const listResult = await alisAPI.listSessions(state.userId);
            console.log('📋 List result:', listResult);
            updateState({ loading: false });

            if (listResult.status === 'success' && listResult.data.sessions.length > 0) {
                const sessions = listResult.data.sessions;
                console.log('✅ Found sessions:', sessions.length);

                // Create selection dialog
                let message = t.session?.selectPrompt || 'Select a session to load:\n\n';
                sessions.forEach((session, index) => {
                    const date = new Date(session.timestamp).toLocaleString();
                    message += `${index + 1}. ${session.session_name || session.goal_name}\n`;
                    message += `   Phase: ${session.phase} | ${date}\n`;
                    message += `   Current: ${session.current_concept}\n\n`;
                });

                const choice = prompt(message + (t.session?.enterNumber || 'Enter number (1-' + sessions.length + '):'));

                if (choice === null) return; // User cancelled

                const selectedIndex = parseInt(choice) - 1;
                if (selectedIndex >= 0 && selectedIndex < sessions.length) {
                    const selectedSession = sessions[selectedIndex];

                    // Load the selected session
                    updateState({ loading: true });
                    const result = await alisAPI.loadSession(state.userId, selectedSession.goal_id);

                    if (result.status === 'success') {
                        const session = result.data;
                        setPhase(session.phase || 'P1_GOAL_SETTING');
                        updateState({
                            loading: false,
                            goalId: session.goal_id,
                            pathStructure: session.path_structure || [],
                            currentConcept: session.current_concept,
                            llmOutput: session.llm_output || '',
                            tutorChat: session.tutor_chat || [],
                            testEvaluationResult: session.test_evaluation_result,
                            parsedTestQuestions: session.parsed_test_questions || [],
                            userTestAnswers: session.user_test_answers || {},
                            remediationNeeded: session.remediation_needed || false
                        });
                        setLanguage(session.language || 'de');
                        alert(t.session?.loaded || 'Session loaded successfully! 📂');
                    }
                } else {
                    alert(t.session?.invalidChoice || 'Invalid selection');
                }
            } else {
                console.log('❌ No sessions found or error:', listResult);
                alert(t.session?.noSession || 'No saved sessions found');
            }
        } catch (error) {
            console.error('❌ Load session error:', error);
            updateState({ loading: false });
            alert(t.session?.noSession || 'No saved sessions found');
        }
    };

    // Auto-save on important actions
    useEffect(() => {
        if (state.goalId && (phase === 'P3_PATH_REVIEW' || phase === 'P5_LEARNING' || phase === 'P7_GOAL_COMPLETE')) {
            autoSaveSession();
        }
    }, [phase, state.goalId]);

    // ==============================================================================
    // 4. PHASE RENDERERS
    // ==============================================================================

    const renderLearningUI = () => (
        <div className="flex flex-col lg:flex-row h-full">
            <div className="w-full lg:w-3/4 p-6 overflow-y-auto bg-white rounded-l-xl shadow-lg">
                <h2 className="text-xl font-bold mb-4 flex items-center text-indigo-700">
                    <BookOpen className="mr-2" /> Learning Phase: {state.currentConcept?.name}
                </h2>
                <div className="p-6 bg-gray-50 text-gray-800 border border-gray-200 rounded-xl shadow-inner min-h-[300px]">
                    {state.loading ? <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin text-indigo-500" /></div> : <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: state.llmOutput.replace(/\n/g, '<br/>') }} />}
                </div>
                <div className="mt-6 flex justify-between items-center">
                    <button onClick={triggerRemediation} className="flex items-center px-4 py-2 bg-red-100 text-red-700 border border-red-300 rounded-full hover:bg-red-200 transition duration-150 shadow-md">
                        <AlertTriangle className="w-4 h-4 mr-2" />
                        Missing Prerequisite (P5.5)
                    </button>
                    <button onClick={startTestGeneration} className="flex items-center px-4 py-2 bg-green-600 text-white rounded-full hover:bg-green-700 transition duration-150 shadow-md" disabled={state.loading}>
                        Concept Understood (Start P6) <ArrowRight className="w-4 h-4 ml-2" />
                    </button>
                </div>
            </div>
            <div className="w-full lg:w-1/4 p-4 border-l border-gray-200 bg-gray-50 text-gray-700 rounded-r-xl flex flex-col">
                <h3 className="text-lg font-semibold mb-3 flex items-center text-gray-700">
                    <MessageCircle className="mr-2 w-5 h-5" /> Tutor Chat
                </h3>
                <div className="flex-grow overflow-y-auto space-y-3 p-2 bg-white rounded-lg shadow-inner mb-4">
                    {state.tutorChat.map((chat, index) => (
                        <div key={index} className={`max-w-[90%] p-2 rounded-lg text-sm ${chat.sender === 'User' ? 'ml-auto bg-indigo-100 text-indigo-800' : 'bg-gray-200 text-gray-800'}`}>
                            <strong>{chat.sender}:</strong> {chat.message}
                        </div>
                    ))}
                </div>
                <div className="flex items-center">
                    <input type="text" placeholder={state.remediationNeeded ? "What prerequisite is missing? (P5.5)" : "Ask the Tutor..."} value={state.userInput} onChange={(e) => updateState({ userInput: e.target.value })} onKeyPress={(e) => e.key === 'Enter' && handleChatOrRemediationInput()} className="flex-grow p-3 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900 bg-white" disabled={state.loading} />
                    <button onClick={handleChatOrRemediationInput} className="p-3 bg-indigo-600 text-white rounded-r-lg hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-400" disabled={state.loading || !state.userInput}>
                        {state.loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowRight className="w-5 h-5" />}
                    </button>
                </div>
                {state.remediationNeeded && <p className="text-xs text-red-500 mt-1">Enter the missing concept to correct the path.</p>}
            </div>
        </div>
    );

    const renderGoalSettingUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-xl mx-auto my-20">
            <h1 className="text-3xl font-extrabold text-indigo-700 mb-4 flex items-center">
                <Zap className="mr-3 w-7 h-7" /> {t.p1.title}
            </h1>
            <p className="text-gray-600 mb-6">
                {t.p1.description}
            </p>
            <textarea className="w-full p-4 border-2 border-indigo-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none min-h-[150px] text-gray-900 bg-white" placeholder={t.p1.placeholder} value={goalInput} onChange={(e) => setGoalInput(e.target.value)} />
            <div className="mt-4 flex items-center justify-center">
                <input type="checkbox" id="pretest-toggle" checked={pretest} onChange={(e) => setPretest(e.target.checked)} className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500" />
                <label htmlFor="pretest-toggle" className="ml-2 block text-sm text-gray-700">
                    {t.p2.choiceDescription}
                </label>
            </div>
            <button onClick={startGoalSetting} className="w-full mt-4 flex items-center justify-center p-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-400" disabled={state.loading || !goalInput}>
                {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <Zap className="mr-2 w-5 h-5" />}
                {state.loading ? t.p1.buttonSubmitting : t.p1.buttonSubmit}
            </button>
            {!state.loading && state.llmOutput && phase !== 'P1_GOAL_SETTING' && (
                <div className="mt-4 p-4 text-sm bg-indigo-50 rounded-lg text-indigo-700 border border-indigo-200">
                    <p>{t.p1.currentMessage} {state.llmOutput.split('\n')[0]}...</p>
                </div>
            )}
        </div>
    );

    const renderPriorKnowledgeTestUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-3xl mx-auto my-10">
            <h1 className="text-3xl font-extrabold text-indigo-700 mb-6 flex items-center">
                <BrainCircuit className="mr-3 w-7 h-7" /> {t.p2.testTitle}
            </h1>
            <p className="text-gray-600 mb-6">
                {t.p2.testDescription}
            </p>
            <div className="space-y-6">
                {state.parsedTestQuestions.map((question, index) => (
                    <div key={question.id || index} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                        <p className="font-semibold text-lg mb-3 text-gray-800">{index + 1}. {question.question_text}</p>
                        {question.type === 'multiple_choice' ? (
                            <div className="space-y-2">
                                {question.options.map((option, optIndex) => (
                                    <label key={optIndex} className="flex items-center space-x-3 cursor-pointer p-2 hover:bg-gray-100 rounded">
                                        <input type="radio" name={question.id} value={option} checked={state.userTestAnswers[question.id] === option} onChange={(e) => handleAnswerChange(question.id, e.target.value)} className="form-radio h-5 w-5 text-indigo-600" />
                                        <span className="text-gray-700">{option}</span>
                                    </label>
                                ))}
                            </div>
                        ) : (
                            <textarea className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 bg-white" rows="3" placeholder={t.p2.yourAnswer} value={state.userTestAnswers[question.id] || ''} onChange={(e) => handleAnswerChange(question.id, e.target.value)} />
                        )}
                    </div>
                ))}
            </div>
            <button onClick={submitPriorKnowledgeTest} className="w-full mt-8 flex items-center justify-center p-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-400" disabled={state.loading}>
                {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <CheckCircle className="mr-2 w-5 h-5" />}
                {t.p2.submitButton}
            </button>
        </div>
    );

    const renderPathReviewUI = () => {
        const hasAvailableConcepts = state.pathStructure.some(c => c.status === 'Open' || c.status === 'Reactivated');
        return (
            <div className="p-8 bg-white rounded-xl shadow-2xl max-w-3xl mx-auto my-10">
                <h1 className="text-3xl font-extrabold text-indigo-700 mb-6 flex items-center">
                    <LayoutList className="mr-3 w-7 h-7" /> {t.p3.title}
                </h1>
                <p className="text-gray-600 mb-6">
                    {t.p3.description}
                </p>
                <ul className="space-y-3 mb-8">
                    {state.pathStructure.map((concept, index) => (
                        <li key={concept.id} className={`flex items-center justify-between p-4 rounded-lg transition duration-150 ${concept.status === 'Active' ? 'bg-indigo-100 border-l-4 border-indigo-600 font-semibold' :
                            concept.status === 'Skipped' || concept.status === 'Mastered' ? 'bg-green-50 line-through text-gray-500' :
                                'bg-gray-50 border border-gray-200 text-gray-700'
                            }`}>
                            <span className="flex items-center">
                                {index + 1}. {concept.name}
                                {(concept.status === 'Skipped' || concept.status === 'Mastered') && <span className="ml-2 text-xs font-bold text-green-700">({concept.status}: {concept.expertiseSource || 'Test'})</span>}
                            </span>
                            <input type="checkbox" checked={concept.status === 'Skipped' || concept.status === 'Mastered'} onChange={() => {
                                const newPath = state.pathStructure.map(c => c.id === concept.id ? { ...c, status: (c.status === 'Skipped' || c.status === 'Mastered') ? 'Open' : 'Skipped', expertiseSource: (c.status === 'Skipped' || c.status === 'Mastered') ? null : 'P3 Expert' } : c);
                                updateState({ pathStructure: newPath });
                            }} className="h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500" />
                        </li>
                    ))}
                </ul>
                {hasAvailableConcepts ? (
                    <button onClick={confirmPathAndStartLearning} className="w-full flex items-center justify-center p-3 bg-green-600 text-white font-semibold rounded-lg shadow-lg hover:bg-green-700 transition duration-150" disabled={state.loading}>
                        {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <BookOpen className="mr-2 w-5 h-5" />}
                        {t.p3.startLearning}
                    </button>
                ) : (
                    <button onClick={() => {
                        updateState({ llmOutput: t.p7.goalComplete.description });
                        setPhase('P7_GOAL_COMPLETE');
                    }} className="w-full flex items-center justify-center p-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150">
                        <CheckCircle className="mr-2 w-5 h-5" />
                        {t.p7.goalComplete.title}
                    </button>
                )}
            </div>
        );
    };

    const renderTestUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-3xl mx-auto my-10">
            <h1 className="text-3xl font-extrabold text-indigo-700 mb-6 flex items-center">
                <Zap className="mr-3 w-7 h-7" /> Test (P6)
            </h1>
            <p className="text-gray-600 mb-6">
                The **Curator** has generated test questions for the concept "{state.currentConcept?.name}". Please answer the questions:
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
                                            <input type="radio" name={`question - ${q.id || `q${qIndex}`}`} value={option} checked={state.userTestAnswers[q.id || `q${qIndex}`] === option} onChange={(e) => handleAnswerChange(q.id || `q${qIndex}`, e.target.value)} className="form-radio text-indigo-600 h-4 w-4" />
                                            <span className="ml-2">{option}</span>
                                        </label>
                                    ))}
                                </div>
                            ) : (
                                <textarea className="w-full p-3 mt-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y min-h-[80px] text-gray-900 bg-white" placeholder="Your answer..." value={state.userTestAnswers[q.id || `q${qIndex}`] || ''} onChange={(e) => handleAnswerChange(q.id || `q${qIndex}`, e.target.value)} />
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <p className="text-red-500">Could not load test questions or the format is invalid.</p>
            )}
            <button onClick={submitTest} className="w-full mt-6 flex items-center justify-center p-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-400" disabled={state.loading}>
                {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <CheckCircle className="mr-2 w-5 h-5" />}
                Submit & Evaluate Test
            </button>
        </div>
    );

    // ==============================================================================
    // P7: ADAPTION & PROGRESSION UIs
    // ==============================================================================

    const renderQuestionResults = () => {
        if (!state.testEvaluationResult?.question_results?.length) return null;
        return (
            <div className="mt-8 text-left">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Detailed Evaluation:</h3>
                <div className="space-y-4">
                    {state.testEvaluationResult.question_results.map((result, index) => (
                        <div key={index} className={`p-4 rounded-lg border ${result.is_correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                            <div className="flex items-start">
                                <div className="flex-shrink-0 mt-1">{result.is_correct ? <CheckCircle className="w-5 h-5 text-green-600" /> : <XCircle className="w-5 h-5 text-red-600" />}</div>
                                <div className="ml-3">
                                    <p className="font-semibold text-gray-900">{result.question_text}</p>
                                    <p className="text-sm mt-1"><span className="font-medium">Your Answer:</span> {result.user_answer}</p>
                                    {!result.is_correct && <p className="text-sm mt-1 text-green-700"><span className="font-medium">Correct Answer:</span> {result.correct_answer}</p>}
                                    <p className="text-sm mt-2 text-gray-600 italic">{result.explanation}</p>
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
                <h1 className="text-3xl font-extrabold text-green-700 mb-4">🎉 Congratulations! Test Passed!</h1>
                <p className="text-gray-600 mb-6">You have successfully mastered the concept <strong>"{state.currentConcept?.name}"</strong>.</p>
                {state.testEvaluationResult && (
                    <div className="bg-green-50 p-4 rounded-lg mb-6">
                        <p className="text-lg font-semibold">Score: {state.testEvaluationResult.score}%</p>
                        <p className="text-gray-700 mt-2">{state.testEvaluationResult.feedback}</p>
                    </div>
                )}
                {renderQuestionResults()}
                <button onClick={async () => {
                    const nextConcept = state.currentConcept;
                    if (!nextConcept) {
                        setPhase('P7_GOAL_COMPLETE');
                        return;
                    }
                    updateState({ loading: true, llmOutput: 'Curator is generating material for the next concept...' });
                    try {
                        const result = await alisAPI.getMaterial(state.userId, state.goalId, state.pathStructure, nextConcept, state.userProfile);
                        updateState({
                            loading: false,
                            llmOutput: result.data.llm_output,
                            tutorChat: [{ sender: 'System', message: `Welcome to the concept: ${nextConcept.name}!` }],
                            testEvaluationResult: null
                        });
                        setPhase('P5_LEARNING');
                    } catch (error) {
                        updateState({ loading: false, llmOutput: `Error: ${error.message}` });
                    }
                }} className="w-full flex items-center justify-center p-4 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150" disabled={state.loading}>
                    {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <ArrowRight className="mr-2 w-5 h-5" />}
                    Continue to Next Concept
                </button>
            </div>
        </div>
    );

    const renderGoalCompleteUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-2xl mx-auto my-20">
            <div className="text-center">
                <CheckCircle className="w-24 h-24 text-green-600 mx-auto mb-6 animate-bounce" />
                <h1 className="text-4xl font-extrabold text-green-700 mb-4">🏆 {t.p7.goalComplete.title}</h1>
                <p className="text-xl text-gray-600 mb-6">{t.p7.goalComplete.description}</p>
                {state.testEvaluationResult && (
                    <div className="bg-green-50 p-6 rounded-lg mb-6">
                        <p className="text-lg font-semibold mb-2">{t.p7.goalComplete.lastTest}</p>
                        <p className="text-2xl font-bold text-green-700">{state.testEvaluationResult.score}%</p>
                        <p className="text-gray-700 mt-2">{state.testEvaluationResult.feedback}</p>
                    </div>
                )}
                {renderQuestionResults()}
                <div className="space-y-3">
                    <button onClick={() => {
                        setPhase('P1_GOAL_SETTING');
                        setGoalInput('');
                        updateState({
                            goalId: null,
                            pathStructure: [],
                            currentConcept: null,
                            llmOutput: "Define your learning goal to start the Architect.",
                            tutorChat: [],
                            testEvaluationResult: null
                        });
                    }} className="w-full flex items-center justify-center p-4 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150">
                        <Zap className="mr-2 w-5 h-5" />
                        {t.p7.goalComplete.newGoal}
                    </button>
                </div>
            </div>
        </div>
    );

    const renderRemediationChoiceUI = () => (
        <div className="p-8 bg-white rounded-xl shadow-2xl max-w-2xl mx-auto my-20">
            <div className="text-center">
                <XCircle className="w-20 h-20 text-red-600 mx-auto mb-4" />
                <h1 className="text-3xl font-extrabold text-red-700 mb-4">Test Not Passed</h1>
                <p className="text-gray-600 mb-6">Don't worry! Learning is a process. Choose how you would like to proceed:</p>
                {state.testEvaluationResult && (
                    <div className="bg-red-50 p-4 rounded-lg mb-6">
                        <p className="text-lg font-semibold">Score: {state.testEvaluationResult.score}%</p>
                        <p className="text-gray-700 mt-2">{state.testEvaluationResult.feedback}</p>
                        {state.testEvaluationResult.recommendation && <p className="text-gray-800 mt-2 font-semibold">💡 Recommendation: {state.testEvaluationResult.recommendation}</p>}
                    </div>
                )}
                {renderQuestionResults()}
                <div className="space-y-3">
                    <button onClick={async () => {
                        updateState({ loading: true, llmOutput: 'Reloading material...' });
                        try {
                            const result = await alisAPI.getMaterial(state.userId, state.goalId, state.pathStructure, state.currentConcept, state.userProfile);
                            updateState({
                                loading: false,
                                llmOutput: result.data.llm_output,
                                tutorChat: [{ sender: 'System', message: 'Let\'s review the concept again!' }],
                                testEvaluationResult: null
                            });
                            setPhase('P5_LEARNING');
                        } catch (error) {
                            updateState({ loading: false, llmOutput: `Error: ${error.message}` });
                        }
                    }} className="w-full flex items-center justify-center p-4 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition duration-150" disabled={state.loading}>
                        {state.loading ? <Loader2 className="mr-2 w-5 h-5 animate-spin" /> : <BookOpen className="mr-2 w-5 h-5" />}
                        Repeat Concept
                    </button>
                    <button onClick={() => {
                        setPhase('P5_LEARNING');
                        updateState({
                            remediationNeeded: true,
                            testEvaluationResult: null,
                            tutorChat: [...state.tutorChat, { sender: 'System', message: 'Use the "Missing Prerequisite" button to identify foundational gaps.' }]
                        });
                    }} className="w-full flex items-center justify-center p-4 bg-yellow-600 text-white font-semibold rounded-lg shadow-lg hover:bg-yellow-700 transition duration-150">
                        <AlertTriangle className="mr-2 w-5 h-5" />
                        Report Prerequisite Gap (P5.5)
                    </button>
                    <button onClick={async () => {
                        if (confirm(t.p7.remediation.skipConcept + '?')) {
                            // Mark as skipped and move to next
                            const nextConcept = state.pathStructure.find((c, i) => i > state.pathStructure.findIndex(pc => pc.id === state.currentConcept.id) && (c.status === 'Open' || c.status === 'Reactivated'));

                            if (nextConcept) {
                                updateState({ loading: true, llmOutput: 'Skipping concept... Generating material for next concept...' });
                                try {
                                    const result = await alisAPI.getMaterial(state.userId, state.goalId, state.pathStructure, nextConcept, state.userProfile);
                                    updateState({
                                        loading: false,
                                        llmOutput: result.data.llm_output,
                                        currentConcept: nextConcept,
                                        tutorChat: [{ sender: 'System', message: `Concept skipped. Welcome to: ${nextConcept.name}!` }],
                                        testEvaluationResult: null
                                    });
                                    setPhase('P5_LEARNING');
                                } catch (error) {
                                    updateState({ loading: false, llmOutput: `Error: ${error.message}` });
                                }
                            } else {
                                setPhase('P7_GOAL_COMPLETE');
                            }
                        }
                    }} className="w-full flex items-center justify-center p-4 bg-gray-500 text-white font-semibold rounded-lg shadow-lg hover:bg-gray-600 transition duration-150">
                        <ArrowRight className="mr-2 w-5 h-5" />
                        {t.p7.remediation.skipConcept}
                    </button>
                </div>
            </div>
        </div >
    );

    // ==============================================================================
    // 5. MAIN LAYOUT & SWITCH
    // ==============================================================================

    return (
        <div className="min-h-screen bg-gray-100 font-sans p-4">
            {/* Session Management & Language Switcher */}
            <div className="fixed top-4 right-4 z-50 flex gap-2">
                <button
                    onClick={handleLoadSession}
                    className="px-3 py-2 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700 transition-all flex items-center gap-1"
                    title={t.session?.load || "Load saved progress"}
                >
                    📂 {t.session?.loadBtn || "Load"}
                </button>
                <button
                    onClick={handleSaveSession}
                    className="px-3 py-2 bg-green-600 text-white rounded-lg shadow-md hover:bg-green-700 transition-all flex items-center gap-1 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    disabled={!state.goalId}
                    title={t.session?.save || "Save current progress"}
                >
                    💾 {t.session?.saveBtn || "Save"}
                </button>
                <select
                    value={language}
                    onChange={(e) => changeLanguage(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                >
                    <option value="de">🇩🇪 Deutsch</option>
                    <option value="en">🇬🇧 English</option>
                </select>
            </div>

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
