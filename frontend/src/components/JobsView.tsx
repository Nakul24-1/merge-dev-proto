import { useState } from 'react';
import { ConfirmDialog } from './ConfirmDialog';
import type { JobDescription } from '../types';
import './JobsView.css';

interface JobsViewProps {
    jobs: JobDescription[];
    onAddClick: () => void;
    onDeleteJob: (jobId: string) => Promise<void>;
    onJobClick?: (job: JobDescription) => void;
}

export function JobsView({ jobs, onAddClick, onDeleteJob, onJobClick }: JobsViewProps) {
    const [deleteTarget, setDeleteTarget] = useState<JobDescription | null>(null);

    const handleDeleteClick = (e: React.MouseEvent, job: JobDescription) => {
        e.stopPropagation();
        e.preventDefault();
        setDeleteTarget(job);
    };

    const handleConfirmDelete = async () => {
        if (deleteTarget?.id) {
            await onDeleteJob(deleteTarget.id);
        }
        setDeleteTarget(null);
    };

    return (
        <div className="jobs-view">
            <div className="jobs-header">
                <div>
                    <h2>Job Descriptions</h2>
                    <p className="jobs-subtitle">{jobs.length} job{jobs.length !== 1 ? 's' : ''} created</p>
                </div>
                <button className="btn btn-primary" onClick={onAddClick}>
                    + Add Job
                </button>
            </div>

            {jobs.length === 0 ? (
                <div className="jobs-empty">
                    <div className="empty-icon">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                        </svg>
                    </div>
                    <h3>No job descriptions yet</h3>
                    <p>Create your first job to start screening candidates</p>
                    <button className="btn btn-primary" onClick={onAddClick}>
                        + Create Job
                    </button>
                </div>
            ) : (
                <div className="jobs-grid">
                    {jobs.map((job) => (
                        <div
                            key={job.id}
                            className="job-card"
                            onClick={() => onJobClick?.(job)}
                            style={{ cursor: onJobClick ? 'pointer' : 'default' }}
                        >
                            <div className="job-card-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                                    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                                </svg>
                            </div>
                            <div className="job-card-content">
                                <h3>{job.title}</h3>
                                {job.company && <p className="job-company">{job.company}</p>}
                                {job.location && <p className="job-location">{job.location}</p>}
                                {job.required_skills && job.required_skills.length > 0 && (
                                    <div className="job-skills">
                                        {job.required_skills.slice(0, 3).map((skill, idx) => (
                                            <span key={idx} className="skill-tag">{skill}</span>
                                        ))}
                                        {job.required_skills.length > 3 && (
                                            <span className="skill-more">+{job.required_skills.length - 3}</span>
                                        )}
                                    </div>
                                )}
                            </div>
                            <div className="job-card-actions">
                                <button
                                    className="btn-delete"
                                    onClick={(e) => handleDeleteClick(e, job)}
                                    title="Delete job"
                                >
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <polyline points="3 6 5 6 21 6" />
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <ConfirmDialog
                isOpen={deleteTarget !== null}
                title="Delete Job"
                message={`Are you sure you want to delete "${deleteTarget?.title}"? This cannot be undone.`}
                onConfirm={handleConfirmDelete}
                onCancel={() => setDeleteTarget(null)}
            />
        </div>
    );
}
