import { useState } from 'react';
import { createJob } from '../api/client';
import type { JobDescription } from '../types';
import './JobForm.css';

interface JobFormProps {
    onJobCreated: (job: JobDescription) => void;
}

export function JobForm({ onJobCreated }: JobFormProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        company: '',
        description: '',
        required_skills: '',
        preferred_skills: '',
        location: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);

        try {
            const job = await createJob({
                title: formData.title,
                company: formData.company || undefined,
                description: formData.description,
                required_skills: formData.required_skills.split(',').map(s => s.trim()).filter(Boolean),
                preferred_skills: formData.preferred_skills.split(',').map(s => s.trim()).filter(Boolean),
                location: formData.location || undefined,
            });

            onJobCreated(job);
            setFormData({
                title: '',
                company: '',
                description: '',
                required_skills: '',
                preferred_skills: '',
                location: '',
            });
            setIsExpanded(false);
        } catch (err) {
            console.error('Failed to create job:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="job-form">
            <div className="job-form-header" onClick={() => setIsExpanded(!isExpanded)}>
                <h2>💼 Add Job Description</h2>
                <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
            </div>

            {isExpanded && (
                <form onSubmit={handleSubmit}>
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
                            placeholder="Describe the role, responsibilities, and qualifications..."
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
                            <label>Preferred Skills</label>
                            <input
                                type="text"
                                value={formData.preferred_skills}
                                onChange={(e) => setFormData({ ...formData, preferred_skills: e.target.value })}
                                placeholder="Docker, Kubernetes (comma-separated)"
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Location</label>
                        <input
                            type="text"
                            value={formData.location}
                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                            placeholder="e.g., Remote, New York, NY"
                        />
                    </div>

                    <button type="submit" className="submit-btn" disabled={isSubmitting}>
                        {isSubmitting ? 'Creating...' : '+ Create Job'}
                    </button>
                </form>
            )}
        </div>
    );
}
