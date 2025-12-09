import type { Candidate } from '../types';
import './CandidateList.css';

interface CandidateListProps {
    candidates: Candidate[];
    selectedCandidate: Candidate | null;
    onSelectCandidate: (candidate: Candidate) => void;
}

export function CandidateList({ candidates, selectedCandidate, onSelectCandidate }: CandidateListProps) {
    if (candidates.length === 0) {
        return (
            <div className="candidate-list empty">
                <h2>👥 Candidates</h2>
                <div className="empty-state">
                    <p>No candidates yet</p>
                    <p className="hint">Upload resumes to get started</p>
                </div>
            </div>
        );
    }

    return (
        <div className="candidate-list">
            <h2>👥 Candidates ({candidates.length})</h2>
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
                            {candidate.current_job_title && (
                                <p className="job-title">{candidate.current_job_title}</p>
                            )}
                            {candidate.current_company && (
                                <p className="company">{candidate.current_company}</p>
                            )}
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
                                <span className="exp-badge">{candidate.years_of_experience}+ yrs</span>
                            )}
                            {candidate.phone && <span className="has-phone">📞</span>}
                            {candidate.email && <span className="has-email">✉️</span>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
