import { useState, useRef } from 'react';
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
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            await handleFile(files[0]);
        }
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            await handleFile(files[0]);
        }
    };

    const handleFile = async (file: File) => {
        setIsUploading(true);
        setError(null);

        try {
            const candidate = await uploadResume(file);
            onUploadSuccess(candidate);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload failed');
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    return (
        <div className="resume-upload">
            <div
                className={`drop-zone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {isUploading ? (
                    <div className="upload-spinner">
                        <div className="spinner"></div>
                        <p>Processing resume...</p>
                    </div>
                ) : (
                    <>
                        <div className="upload-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                <polyline points="14 2 14 8 20 8" />
                                <line x1="12" y1="18" x2="12" y2="12" />
                                <line x1="9" y1="15" x2="12" y2="12" />
                                <line x1="15" y1="15" x2="12" y2="12" />
                            </svg>
                        </div>
                        <p>Drag and drop a resume here</p>
                        <span className="or-text">or</span>
                        <label className="file-input-label">
                            Browse Files
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".pdf,.doc,.docx,.txt"
                                onChange={handleFileSelect}
                                style={{ display: 'none' }}
                            />
                        </label>
                        <p className="file-types">PDF, DOC, DOCX, or TXT</p>
                    </>
                )}
            </div>
            {error && <div className="error-message">{error}</div>}
        </div>
    );
}
