import { useState } from 'react';
import { ConfirmDialog } from './ConfirmDialog';
import type { Candidate } from '../types';
import './CandidateList.css';

interface CandidateListProps {
    candidates: Candidate[];
    selectedCandidate: Candidate | null;
    onSelectCandidate: (candidate: Candidate) => void;
    onAddCandidate?: () => void;
    onDeleteCandidate?: (candidateId: string) => Promise<void>;
}

export function CandidateList({ candidates, selectedCandidate, onSelectCandidate, onDeleteCandidate }: CandidateListProps) {
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const [deleteTarget, setDeleteTarget] = useState<Candidate | null>(null);

    const handleDeleteClick = (e: React.MouseEvent, candidate: Candidate) => {
        e.stopPropagation();
        if (!onDeleteCandidate || !candidate.id) return;
        setDeleteTarget(candidate);
    };

    const handleConfirmDelete = async () => {
        if (!onDeleteCandidate || !deleteTarget?.id) return;

        setDeletingId(deleteTarget.id);
        try {
            await onDeleteCandidate(deleteTarget.id);
        } catch (error) {
            console.error("Delete failed", error);
        } finally {
            setDeletingId(null);
            setDeleteTarget(null);
        }
    };

    if (candidates.length === 0) {
        return (
            <div className="candidate-list empty">
                <div className="empty-state">
                    <p>No candidates yet</p>
                    <p className="hint">Upload a resume to get started</p>
                </div>
            </div>
        );
    }

    return (
        <>
            <div className="candidate-list">
                <div className="candidates-grid">
                    {candidates.map((candidate) => (
                        <div
                            key={candidate.id}
                            className={`candidate-card ${selectedCandidate?.id === candidate.id ? 'selected' : ''}`}
                            onClick={() => onSelectCandidate(candidate)}
                        >
                            <div className="candidate-avatar">
                                {candidate.full_name.charAt(0).toUpperCase()}
                            </div>
                            <div className="candidate-info">
                                <h3>{candidate.full_name}</h3>
                                <p className="candidate-subtitle">
                                    {candidate.current_job_title}
                                    {candidate.current_job_title && candidate.current_company && ' • '}
                                    {candidate.current_company && (
                                        <span className="company">{candidate.current_company}</span>
                                    )}
                                </p>
                                <div className="skills-preview">
                                    {candidate.skills.slice(0, 3).map((skill, idx) => (
                                        <span key={idx} className="skill-tag">{skill}</span>
                                    ))}
                                    {candidate.skills.length > 3 && (
                                        <span className="skill-more">+{candidate.skills.length - 3}</span>
                                    )}
                                </div>
                            </div>
                            <div className="candidate-meta">
                                {candidate.years_of_experience && (
                                    <span className="exp-text">{candidate.years_of_experience} yrs</span>
                                )}
                                <div className="action-row">
                                    {onDeleteCandidate && candidate.id && (
                                        <button
                                            className="delete-btn"
                                            onClick={(e) => handleDeleteClick(e, candidate)}
                                            title="Delete"
                                            disabled={deletingId === candidate.id}
                                        >
                                            ×
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <ConfirmDialog
                isOpen={deleteTarget !== null}
                title="Delete Candidate"
                message={`Are you sure you want to delete ${deleteTarget?.full_name}? This cannot be undone.`}
                onConfirm={handleConfirmDelete}
                onCancel={() => setDeleteTarget(null)}
            />
        </>
    );
}
