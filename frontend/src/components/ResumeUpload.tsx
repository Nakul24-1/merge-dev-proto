import { useState, useCallback } from 'react';
import { uploadResume } from '../api/client';
import type { Candidate } from '../types';
import './ResumeUpload.css';

interface ResumeUploadProps {
    onUploadSuccess: (candidate: Candidate) => void;
}

export function ResumeUpload({ onUploadSuccess }: ResumeUploadProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback(async (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            await handleFileUpload(files[0]);
        }
    }, []);

    const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            await handleFileUpload(files[0]);
        }
    }, []);

    const handleFileUpload = async (file: File) => {
        setIsUploading(true);
        setError(null);

        try {
            const candidate = await uploadResume(file);
            onUploadSuccess(candidate);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload failed');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="resume-upload">
            <h2>📄 Upload Resume</h2>

            <div
                className={`drop-zone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {isUploading ? (
                    <div className="upload-spinner">
                        <div className="spinner"></div>
                        <p>Parsing resume...</p>
                    </div>
                ) : (
                    <>
                        <div className="upload-icon">📁</div>
                        <p>Drag & drop resume here</p>
                        <p className="or-text">or</p>
                        <label className="file-input-label">
                            Browse Files
                            <input
                                type="file"
                                accept=".pdf,.doc,.docx,.txt"
                                onChange={handleFileSelect}
                                hidden
                            />
                        </label>
                        <p className="file-types">PDF, DOC, DOCX, TXT</p>
                    </>
                )}
            </div>

            {error && <div className="error-message">❌ {error}</div>}
        </div>
    );
}
