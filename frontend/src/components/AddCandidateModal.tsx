import { useState } from 'react';
import { uploadResume } from '../api/client';
import type { Candidate } from '../types';
import './AddCandidateModal.css';

interface AddCandidateModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCandidateAdded: (candidate: Candidate) => void;
}

export function AddCandidateModal({ isOpen, onClose, onCandidateAdded }: AddCandidateModalProps) {
    const [dragActive, setDragActive] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            await handleFile(e.dataTransfer.files[0]);
        }
    };

    const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            await handleFile(e.target.files[0]);
        }
    };

    const handleFile = async (file: File) => {
        setIsUploading(true);
        setError(null);

        try {
            const candidate = await uploadResume(file);
            onCandidateAdded(candidate);
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to upload resume');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Add New Candidate</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="modal-body">
                    {error && (
                        <div className="upload-error">
                            {error}
                        </div>
                    )}

                    <div
                        className={`drop-zone ${dragActive ? 'active' : ''} ${isUploading ? 'uploading' : ''}`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                    >
                        {isUploading ? (
                            <>
                                <div className="spinner"></div>
                                <p>Parsing resume...</p>
                            </>
                        ) : (
                            <>
                                <div className="drop-icon">
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                        <polyline points="14 2 14 8 20 8" />
                                        <line x1="12" y1="18" x2="12" y2="12" />
                                        <line x1="9" y1="15" x2="12" y2="12" />
                                        <line x1="15" y1="15" x2="12" y2="12" />
                                    </svg>
                                </div>
                                <p className="drop-main">Drag & drop resume here</p>
                                <p className="drop-sub">or click to browse</p>
                                <p className="drop-formats">PDF, DOCX, DOC, TXT</p>
                                <input
                                    type="file"
                                    accept=".pdf,.doc,.docx,.txt"
                                    onChange={handleFileInput}
                                    className="file-input"
                                />
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
