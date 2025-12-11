import { useState } from 'react';
import { createJob } from '../api/client';
import type { JobDescription } from '../types';
import './AddJobModal.css';

interface AddJobModalProps {
    isOpen: boolean;
    onClose: () => void;
    onJobCreated: (job: JobDescription) => void;
}

export function AddJobModal({ isOpen, onClose, onJobCreated }: AddJobModalProps) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [formData, setFormData] = useState({
        title: '',
        company: '',
        description: '',
        required_skills: '',
        location: '',
    });

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title || !formData.description) return;

        setIsSubmitting(true);
        setError(null);

        try {
            const job = await createJob({
                title: formData.title,
                company: formData.company || undefined,
                description: formData.description,
                required_skills: formData.required_skills.split(',').map(s => s.trim()).filter(Boolean),
                preferred_skills: [],
                location: formData.location || undefined,
            });

            onJobCreated(job);
            setFormData({ title: '', company: '', description: '', required_skills: '', location: '' });
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create job');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>New Job Description</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <form className="modal-body" onSubmit={handleSubmit}>
                    {error && <div className="form-error">{error}</div>}

                    <div className="form-row">
                        <div className="form-group">
                            <label>Job Title *</label>
                            <input
                                type="text"
                                value={formData.title}
                                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                placeholder="e.g., Senior Software Engineer"
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Company</label>
                            <input
                                type="text"
                                value={formData.company}
                                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                                placeholder="e.g., Acme Corp"
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Job Description *</label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            placeholder="Describe the role, responsibilities, and requirements..."
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
                                placeholder="Python, React, AWS (comma-separated)"
                            />
                        </div>
                        <div className="form-group">
                            <label>Location</label>
                            <input
                                type="text"
                                value={formData.location}
                                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                placeholder="e.g., Remote, NYC"
                            />
                        </div>
                    </div>

                    <div className="modal-actions">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                            {isSubmitting ? 'Creating...' : 'Create Job'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
