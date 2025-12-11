import { useState, useEffect } from 'react';
import { updateJob } from '../api/client';
import { ConfirmDialog } from './ConfirmDialog';
import type { JobDescription } from '../types';
import './AddJobModal.css';

interface JobDetailModalProps {
    isOpen: boolean;
    job: JobDescription | null;
    onClose: () => void;
    onJobUpdated: (job: JobDescription) => void;
    onJobDeleted: (jobId: string) => Promise<void>;
}

export function JobDetailModal({ isOpen, job, onClose, onJobUpdated, onJobDeleted }: JobDetailModalProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [formData, setFormData] = useState({
        title: '',
        company: '',
        description: '',
        required_skills: '',
        location: '',
    });

    useEffect(() => {
        if (job) {
            setFormData({
                title: job.title || '',
                company: job.company || '',
                description: job.description || '',
                required_skills: (job.required_skills || []).join(', '),
                location: job.location || '',
            });
            setIsEditing(false);
            setShowDeleteConfirm(false);
        }
    }, [job]);

    if (!isOpen || !job) return null;

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!job.id) return;

        setIsSubmitting(true);
        setError(null);

        try {
            const updatedJob = await updateJob(job.id, {
                title: formData.title,
                company: formData.company || undefined,
                description: formData.description,
                required_skills: formData.required_skills.split(',').map(s => s.trim()).filter(Boolean),
                preferred_skills: job.preferred_skills || [],
                location: formData.location || undefined,
            });

            onJobUpdated(updatedJob);
            setIsEditing(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update job');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleConfirmDelete = async () => {
        if (job?.id) {
            try {
                await onJobDeleted(job.id);
                onClose();
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to delete job');
            }
        }
        setShowDeleteConfirm(false);
    };

    return (
        <>
            <div className="modal-overlay" onClick={onClose}>
                <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
                    <div className="modal-header">
                        <h2>{isEditing ? 'Edit Job' : 'Job Details'}</h2>
                        <button className="close-btn" onClick={onClose}>×</button>
                    </div>

                    <div className="modal-body">
                        {error && <div className="form-error">{error}</div>}

                        {isEditing ? (
                            <form onSubmit={handleSave}>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Job Title *</label>
                                        <input
                                            type="text"
                                            value={formData.title}
                                            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Company</label>
                                        <input
                                            type="text"
                                            value={formData.company}
                                            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Job Description *</label>
                                    <textarea
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        rows={4}
                                        required
                                    />
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Required Skills</label>
                                        <input
                                            type="text"
                                            value={formData.required_skills}
                                            onChange={(e) => setFormData({ ...formData, required_skills: e.target.value })}
                                            placeholder="Python, React (comma-separated)"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Location</label>
                                        <input
                                            type="text"
                                            value={formData.location}
                                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div className="modal-actions">
                                    <button type="button" className="btn btn-secondary" onClick={() => setIsEditing(false)}>
                                        Cancel
                                    </button>
                                    <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                                        {isSubmitting ? 'Saving...' : 'Save Changes'}
                                    </button>
                                </div>
                            </form>
                        ) : (
                            <div className="job-detail-view">
                                <div className="detail-row">
                                    <span className="detail-label">Title</span>
                                    <span className="detail-value">{job.title}</span>
                                </div>
                                {job.company && (
                                    <div className="detail-row">
                                        <span className="detail-label">Company</span>
                                        <span className="detail-value">{job.company}</span>
                                    </div>
                                )}
                                {job.location && (
                                    <div className="detail-row">
                                        <span className="detail-label">Location</span>
                                        <span className="detail-value">{job.location}</span>
                                    </div>
                                )}
                                <div className="detail-row">
                                    <span className="detail-label">Description</span>
                                    <p className="detail-value detail-description">{job.description}</p>
                                </div>
                                {job.required_skills && job.required_skills.length > 0 && (
                                    <div className="detail-row">
                                        <span className="detail-label">Required Skills</span>
                                        <div className="detail-skills">
                                            {job.required_skills.map((skill, idx) => (
                                                <span key={idx} className="skill-tag">{skill}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <div className="modal-actions">
                                    <button className="btn btn-danger" onClick={() => setShowDeleteConfirm(true)}>
                                        Delete
                                    </button>
                                    <button className="btn btn-primary" onClick={() => setIsEditing(true)}>
                                        Edit
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <ConfirmDialog
                isOpen={showDeleteConfirm}
                title="Delete Job"
                message={`Are you sure you want to delete "${job.title}"? This cannot be undone.`}
                onConfirm={handleConfirmDelete}
                onCancel={() => setShowDeleteConfirm(false)}
            />
        </>
    );
}
