import { useState, useEffect } from 'react';
import { useMergeLink } from '@mergeapi/react-merge-link';
import './ATSConnect.css';

interface ATSConnectProps {
    userId: string;
    onConnected?: () => void;
}

// Use Vite env variable, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export function ATSConnect({ userId, onConnected }: ATSConnectProps) {
    const [linkToken, setLinkToken] = useState<string | null>(null);
    const [atsConnected, setAtsConnected] = useState(false);
    const [crmConnected, setCrmConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showAtsMenu, setShowAtsMenu] = useState(false);
    const [showCrmMenu, setShowCrmMenu] = useState(false);

    useEffect(() => {
        checkConnectionStatus();
    }, [userId]);

    const checkConnectionStatus = async () => {
        try {
            await fetch(`${API_BASE_URL}/merge/sync-connections/${userId}`, { method: 'POST' });
            const statusRes = await fetch(`${API_BASE_URL}/merge/status/${userId}`);
            const statusData = await statusRes.json();
            setAtsConnected(statusData.ats_connected || false);
            setCrmConnected(statusData.crm_connected || false);
        } catch (err) {
            console.error('Failed to check status:', err);
        }
    };

    const getLinkToken = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/merge/link-token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    organization_name: 'Demo Company',
                    email: 'demo@example.com',
                    categories: ['ats', 'crm']
                })
            });
            if (!response.ok) throw new Error('Failed to get link token');
            const data = await response.json();
            setLinkToken(data.link_token);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to initialize');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSync = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/merge/sync/${userId}`, { method: 'POST' });
            const result = await response.json();
            if (response.ok) {
                onConnected?.();
                alert(`Synced ${result.candidates_synced} candidates & ${result.jobs_synced} jobs`);
            } else {
                throw new Error(result.detail || 'Sync failed');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Sync failed');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDisconnect = async (category: 'ats' | 'crm') => {
        if (!confirm(`Are you sure you want to disconnect the ${category.toUpperCase()} integration?`)) {
            return;
        }
        setIsLoading(true);
        try {
            // Note: Backend disconnect endpoint would need to be implemented
            // For now, we just update local state
            if (category === 'ats') {
                setAtsConnected(false);
            } else {
                setCrmConnected(false);
            }
            alert(`${category.toUpperCase()} disconnected. You may need to reconnect via Merge dashboard.`);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Disconnect failed');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSuccess = async (publicToken: string) => {
        setIsLoading(true);
        try {
            const connectResponse = await fetch(`${API_BASE_URL}/merge/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, public_token: publicToken })
            });
            const connectData = await connectResponse.json();
            if (connectData.success) {
                await fetch(`${API_BASE_URL}/merge/sync-connections/${userId}`, { method: 'POST' });
                await checkConnectionStatus();
                await handleSync();
            } else {
                setError(connectData.message);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to connect');
        } finally {
            setIsLoading(false);
            setLinkToken(null);
        }
    };

    const { open, isReady } = useMergeLink({
        linkToken: linkToken || '',
        onSuccess: handleSuccess,
        onExit: () => setLinkToken(null)
    });

    useEffect(() => {
        if (linkToken && isReady) open();
    }, [linkToken, isReady, open]);

    const isConnected = atsConnected || crmConnected;

    return (
        <div className="integration-bar">
            {error && <span className="integration-error">{error}</span>}

            <div className="integration-status">
                <div
                    className={`status-item ${atsConnected ? 'connected' : ''} ${atsConnected ? 'clickable' : ''}`}
                    onClick={() => atsConnected && setShowAtsMenu(!showAtsMenu)}
                >
                    <span className="status-dot"></span>
                    <span className="status-label">ATS</span>
                    {showAtsMenu && atsConnected && (
                        <div className="status-dropdown">
                            <button onClick={(e) => { e.stopPropagation(); handleSync(); setShowAtsMenu(false); }}>
                                Sync Now
                            </button>
                            <button onClick={(e) => { e.stopPropagation(); handleDisconnect('ats'); setShowAtsMenu(false); }}>
                                Disconnect
                            </button>
                        </div>
                    )}
                </div>
                <div
                    className={`status-item ${crmConnected ? 'connected' : ''} ${crmConnected ? 'clickable' : ''}`}
                    onClick={() => crmConnected && setShowCrmMenu(!showCrmMenu)}
                >
                    <span className="status-dot"></span>
                    <span className="status-label">CRM</span>
                    {showCrmMenu && crmConnected && (
                        <div className="status-dropdown">
                            <button onClick={(e) => { e.stopPropagation(); handleSync(); setShowCrmMenu(false); }}>
                                Sync Now
                            </button>
                            <button onClick={(e) => { e.stopPropagation(); handleDisconnect('crm'); setShowCrmMenu(false); }}>
                                Disconnect
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Always show Manage Connections button */}
            <button
                className="btn btn-manage-connections"
                onClick={getLinkToken}
                disabled={isLoading}
                title="Add or manage CRM & ATS integrations"
            >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
                {isLoading ? 'Loading...' : 'Manage Connections'}
            </button>

            {/* Sync button when connected */}
            {isConnected && (
                <button className="btn btn-secondary btn-sm" onClick={handleSync} disabled={isLoading}>
                    {isLoading ? 'Syncing...' : 'Sync'}
                </button>
            )}
        </div>
    );
}
