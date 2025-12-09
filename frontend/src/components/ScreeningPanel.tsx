import { useState } from 'react';
import { generateQuestions, initiateCall } from '../api/client';
import type { Candidate, JobDescription, ScreeningQuestion, CallStatus } from '../types';
import './ScreeningPanel.css';

interface ScreeningPanelProps {
    candidate: Candidate | null;
    jobs: JobDescription[];
}

export function ScreeningPanel({ candidate, jobs }: ScreeningPanelProps) {
    const [selectedJobId, setSelectedJobId] = useState<string>('');
    const [questions, setQuestions] = useState<ScreeningQuestion[]>([]);
    const [callStatus, setCallStatus] = useState<CallStatus | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [loadingAction, setLoadingAction] = useState<'questions' | 'call' | null>(null);
    const [error, setError] = useState<string | null>(null);

    if (!candidate) {
        return (
            <div className="screening-panel empty">
                <h2>🎯 Screening Panel</h2>
                <div className="empty-state">
                    <p>Select a candidate to start screening</p>
                </div>
            </div>
        );
    }

    const handleGenerateQuestions = async () => {
        if (!selectedJobId) return;

        setIsLoading(true);
        setLoadingAction('questions');
        setError(null);

        try {
            const generatedQuestions = await generateQuestions(candidate.id!, selectedJobId);
            setQuestions(generatedQuestions);
        } catch (err) {
            console.error('Failed to generate questions:', err);
            setError(err instanceof Error ? err.message : 'Failed to generate questions');
        } finally {
            setIsLoading(false);
            setLoadingAction(null);
        }
    };

    const handleInitiateCall = async () => {
        if (!selectedJobId || !candidate.phone) return;

        setIsLoading(true);
        setLoadingAction('call');
        setError(null);

        try {
            const status = await initiateCall(candidate.id!, selectedJobId);
            setCallStatus(status);
        } catch (err) {
            console.error('Failed to initiate call:', err);
            setError(err instanceof Error ? err.message : 'Failed to initiate call');
        } finally {
            setIsLoading(false);
            setLoadingAction(null);
        }
    };

    const selectedJob = jobs.find(j => j.id === selectedJobId);

    return (
        <div className="screening-panel">
            <h2>🎯 Screening Panel</h2>

            <div className="candidate-detail">
                <div className="detail-header">
                    <div className="avatar-large">
                        {candidate.full_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <h3>{candidate.full_name}</h3>
                        <p>{candidate.current_job_title || 'No title'}</p>
                        <div className="contact-info">
                            {candidate.phone && <span>📞 {candidate.phone}</span>}
                            {candidate.email && <span>✉️ {candidate.email}</span>}
                        </div>
                    </div>
                </div>

                <div className="skills-section">
                    <h4>Skills</h4>
                    <div className="skills-list">
                        {candidate.skills.length > 0 ? (
                            candidate.skills.map((skill, idx) => (
                                <span key={idx} className="skill-badge">{skill}</span>
                            ))
                        ) : (
                            <span className="no-skills">No skills parsed</span>
                        )}
                    </div>
                </div>
            </div>

            <div className="job-selection">
                <h4>Select Job for Screening</h4>
                {jobs.length === 0 ? (
                    <p className="no-jobs">Add a job description first</p>
                ) : (
                    <select
                        value={selectedJobId}
                        onChange={(e) => setSelectedJobId(e.target.value)}
                    >
                        <option value="">Choose a job...</option>
                        {jobs.map((job) => (
                            <option key={job.id} value={job.id}>
                                {job.title} {job.company && `@ ${job.company}`}
                            </option>
                        ))}
                    </select>
                )}
            </div>

            {error && (
                <div className="error-banner">
                    <span>⚠️</span>
                    <p>{error}</p>
                    <button onClick={() => setError(null)}>✕</button>
                </div>
            )}

            {selectedJob && (
                <div className="action-buttons">
                    <button
                        className="btn-generate"
                        onClick={handleGenerateQuestions}
                        disabled={isLoading}
                    >
                        {loadingAction === 'questions' ? '⏳ Generating...' : '✨ Generate Questions'}
                    </button>

                    <button
                        className="btn-call"
                        onClick={handleInitiateCall}
                        disabled={isLoading || !candidate.phone}
                        title={!candidate.phone ? 'No phone number available' : ''}
                    >
                        {loadingAction === 'call' ? '📞 Calling...' : '📞 Start Screening Call'}
                    </button>
                </div>
            )}

            {questions.length > 0 && (
                <div className="questions-preview">
                    <h4>📝 Generated Questions ({questions.length})</h4>
                    <ul>
                        {questions.map((q, idx) => (
                            <li key={idx}>
                                <span className="q-category">{q.category}</span>
                                <span className="q-text">{q.question}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {callStatus && (
                <div className={`call-status status-${callStatus.status}`}>
                    <h4>📞 Call Status</h4>
                    <div className="status-row">
                        <span className="status-label">Status:</span>
                        <span className={`status-badge ${callStatus.status}`}>
                            {callStatus.status.toUpperCase()}
                        </span>
                    </div>
                    <div className="status-details">
                        <p><span>Call ID:</span> <code>{callStatus.call_id}</code></p>
                        {callStatus.conversation_id && (
                            <p><span>Conversation:</span> <code>{callStatus.conversation_id}</code></p>
                        )}
                        {callStatus.call_sid && (
                            <p><span>Twilio SID:</span> <code>{callStatus.call_sid}</code></p>
                        )}
                    </div>
                    {callStatus.status === 'initiated' && (
                        <p className="call-info">
                            📱 The AI is now calling {candidate.full_name}...
                        </p>
                    )}
                    {callStatus.transcript && (
                        <div className="transcript">
                            <h5>Transcript</h5>
                            <pre>{callStatus.transcript}</pre>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

