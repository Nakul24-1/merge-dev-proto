import { useState } from 'react';
import { generateQuestions, initiateCall } from '../api/client';
import type { Candidate, JobDescription, ScreeningQuestion, CallStatus } from '../types';
import './ScreeningPanel.css';

interface ScreeningPanelProps {
    candidate: Candidate | null;
    jobs: JobDescription[];
    onPushToCrm?: (candidateId: string) => Promise<void>;
}

export function ScreeningPanel({ candidate, jobs, onPushToCrm }: ScreeningPanelProps) {
    const [selectedJobId, setSelectedJobId] = useState<string>('');
    const [questions, setQuestions] = useState<ScreeningQuestion[]>([]);
    const [callStatus, setCallStatus] = useState<CallStatus | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [loadingAction, setLoadingAction] = useState<'questions' | 'call' | 'crm' | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [phoneOverride, setPhoneOverride] = useState<string>('');
    const [showAdvanced, setShowAdvanced] = useState(false);

    if (!candidate) {
        return (
            <div className="screening-panel empty">
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
            setError(err instanceof Error ? err.message : 'Failed to generate questions');
        } finally {
            setIsLoading(false);
            setLoadingAction(null);
        }
    };

    const handleInitiateCall = async () => {
        const phoneToCall = phoneOverride.trim() || candidate.phone;
        if (!selectedJobId || !phoneToCall) return;
        setIsLoading(true);
        setLoadingAction('call');
        setError(null);
        try {
            const status = await initiateCall(candidate.id!, selectedJobId, undefined, undefined, phoneToCall);
            setCallStatus(status);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to initiate call');
        } finally {
            setIsLoading(false);
            setLoadingAction(null);
        }
    };

    const handlePushToCrm = async () => {
        if (!onPushToCrm || !candidate.id) return;
        setIsLoading(true);
        setLoadingAction('crm');
        try {
            await onPushToCrm(candidate.id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to push to CRM');
        } finally {
            setIsLoading(false);
            setLoadingAction(null);
        }
    };

    const selectedJob = jobs.find(j => j.id === selectedJobId);
    const effectivePhone = phoneOverride.trim() || candidate.phone;

    return (
        <div className="screening-panel">
            <div className="panel-header">
                <h2>Screening</h2>
            </div>

            <div className="candidate-detail">
                <div className="detail-header">
                    <div className="avatar-large">
                        {candidate.full_name.charAt(0).toUpperCase()}
                    </div>
                    <div className="detail-info">
                        <h3>{candidate.full_name}</h3>
                        <p>{candidate.current_job_title || 'No title'}</p>
                        <div className="contact-info">
                            {candidate.phone && <span>Phone: {candidate.phone}</span>}
                            {candidate.email && <span>Email: {candidate.email}</span>}
                        </div>
                    </div>
                </div>

                {/* Big CRM Button */}
                {onPushToCrm && (
                    <button
                        className="btn-crm-large"
                        onClick={handlePushToCrm}
                        disabled={isLoading}
                    >
                        {loadingAction === 'crm' ? 'Pushing...' : 'Add to HubSpot CRM'}
                    </button>
                )}

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
                    <p>{error}</p>
                    <button onClick={() => setError(null)}>×</button>
                </div>
            )}

            {selectedJob && (
                <>
                    <div className="phone-override">
                        <label htmlFor="phone-override">Test Phone Number (optional)</label>
                        <input
                            id="phone-override"
                            type="tel"
                            placeholder={candidate.phone || "Enter phone number (+1234567890)"}
                            value={phoneOverride}
                            onChange={(e) => setPhoneOverride(e.target.value)}
                        />
                        {phoneOverride && (
                            <span className="phone-note">
                                Calling: {phoneOverride} (instead of {candidate.phone || 'N/A'})
                            </span>
                        )}
                    </div>

                    <div className="action-buttons">
                        <button
                            className="btn-call"
                            onClick={handleInitiateCall}
                            disabled={isLoading || !effectivePhone}
                        >
                            {loadingAction === 'call' ? 'Calling...' : 'Start Screening Call'}
                        </button>
                    </div>

                    {/* Advanced - Generate Questions (subtle) */}
                    <div className="advanced-section">
                        <button
                            className="advanced-toggle"
                            onClick={() => setShowAdvanced(!showAdvanced)}
                        >
                            {showAdvanced ? '▼ Hide Advanced' : '▶ Advanced Options'}
                        </button>
                        {showAdvanced && (
                            <div className="advanced-content">
                                <button
                                    className="btn-generate"
                                    onClick={handleGenerateQuestions}
                                    disabled={isLoading}
                                >
                                    {loadingAction === 'questions' ? 'Generating...' : 'Generate Questions'}
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}

            {questions.length > 0 && (
                <div className="questions-preview">
                    <h4>Generated Questions ({questions.length})</h4>
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
                    <h4>Call Status</h4>
                    <div className="status-row">
                        <span className="status-label">Status:</span>
                        <span className={`status-badge ${callStatus.status}`}>
                            {callStatus.status.toUpperCase()}
                        </span>
                    </div>
                    {callStatus.status === 'initiated' && (
                        <p className="call-info">
                            The AI is now calling {candidate.full_name}...
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}
