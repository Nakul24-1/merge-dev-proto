import './AddJobModal.css'; // Reuse modal styling

interface ConfirmDialogProps {
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
}

export function ConfirmDialog({ isOpen, title, message, onConfirm, onCancel }: ConfirmDialogProps) {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{title}</h2>
                </div>
                <div className="modal-body">
                    <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>{message}</p>
                    <div className="modal-actions">
                        <button className="btn btn-secondary" onClick={onCancel}>
                            Cancel
                        </button>
                        <button className="btn btn-danger" onClick={onConfirm}>
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
