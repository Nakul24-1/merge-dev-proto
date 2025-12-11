import { useState, useEffect } from 'react';
import { ATSConnect } from './components/ATSConnect';
import { CandidateList } from './components/CandidateList';
import { JobsView } from './components/JobsView';
import { ScreeningPanel } from './components/ScreeningPanel';
import { AddCandidateModal } from './components/AddCandidateModal';
import { AddJobModal } from './components/AddJobModal';
import { JobDetailModal } from './components/JobDetailModal';
import { getCandidates, getJobs, deleteCandidate, deleteJob } from './api/client';
import type { Candidate, JobDescription } from './types';
import './App.css';

type View = 'screening' | 'jobs';

function App() {
  const [currentView, setCurrentView] = useState<View>('screening');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [showAddCandidateModal, setShowAddCandidateModal] = useState(false);
  const [showAddJobModal, setShowAddJobModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState<JobDescription | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [candidatesData, jobsData] = await Promise.all([
        getCandidates(),
        getJobs(),
      ]);
      setCandidates(candidatesData);
      setJobs(jobsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  };

  const handleUploadSuccess = (candidate: Candidate) => {
    setCandidates(prev => [candidate, ...prev]);
    setSelectedCandidate(candidate);
    setCurrentView('screening');
  };

  const handleJobCreated = (job: JobDescription) => {
    setJobs(prev => [job, ...prev]);
  };

  const handleJobUpdated = (updatedJob: JobDescription) => {
    setJobs(prev => prev.map(j => j.id === updatedJob.id ? updatedJob : j));
    setSelectedJob(null);
  };

  const handleDeleteCandidate = async (candidateId: string) => {
    try {
      await deleteCandidate(candidateId);
      setCandidates(prev => prev.filter(c => c.id !== candidateId));
      if (selectedCandidate?.id === candidateId) {
        setSelectedCandidate(null);
      }
    } catch (err) {
      alert(`Failed to delete: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    console.log('handleDeleteJob called with:', jobId);
    try {
      console.log('Calling deleteJob API...');
      await deleteJob(jobId);
      console.log('deleteJob API success');
      setJobs(prev => prev.filter(j => j.id !== jobId));
    } catch (err) {
      console.error('handleDeleteJob error:', err);
      alert(`Failed to delete: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const pushToCrm = async (candidateId: string) => {
    const candidate = candidates.find(c => c.id === candidateId);
    if (!candidate) return;
    const confirmed = window.confirm(`Push ${candidate.full_name} to HubSpot CRM?`);
    if (!confirmed) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/merge/crm/push-candidate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: "user_123", candidate_id: candidateId })
      });
      const result = await response.json();
      if (response.ok) {
        alert(`Successfully pushed to HubSpot!\nContact ID: ${result.crm_contact_id}`);
      } else {
        throw new Error(result.detail || "Failed to push to CRM");
      }
    } catch (err) {
      alert(`CRM Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <div className="logo">
            <div className="logo-icon">AI</div>
            <h1>Candidate Screener</h1>
          </div>
          <nav className="view-nav">
            <button
              className={`nav-item ${currentView === 'screening' ? 'active' : ''}`}
              onClick={() => setCurrentView('screening')}
            >
              Screening
            </button>
            <button
              className={`nav-item ${currentView === 'jobs' ? 'active' : ''}`}
              onClick={() => setCurrentView('jobs')}
            >
              Jobs
            </button>
          </nav>
        </div>
        <ATSConnect userId="user_123" onConnected={loadData} />
      </header>

      <main className="main-content">
        {currentView === 'screening' ? (
          <div className="split-layout">
            <aside className="sidebar">
              <div className="sidebar-header">
                <h2>Candidates ({candidates.length})</h2>
                <button className="btn btn-primary btn-sm" onClick={() => setShowAddCandidateModal(true)}>
                  + Add
                </button>
              </div>
              <div className="sidebar-content">
                <CandidateList
                  candidates={candidates}
                  selectedCandidate={selectedCandidate}
                  onSelectCandidate={setSelectedCandidate}
                  onDeleteCandidate={handleDeleteCandidate}
                />
              </div>
            </aside>
            <section className="workspace">
              {selectedCandidate ? (
                <ScreeningPanel
                  candidate={selectedCandidate}
                  jobs={jobs}
                  onPushToCrm={pushToCrm}
                />
              ) : (
                <div className="workspace-empty">
                  <h3>Select a candidate</h3>
                  <p>Choose someone from the list to start screening</p>
                  <button className="btn btn-secondary" onClick={() => setShowAddCandidateModal(true)}>
                    Upload Resume
                  </button>
                </div>
              )}
            </section>
          </div>
        ) : (
          <JobsView
            jobs={jobs}
            onAddClick={() => setShowAddJobModal(true)}
            onDeleteJob={handleDeleteJob}
            onJobClick={setSelectedJob}
          />
        )}
      </main>

      <AddCandidateModal
        isOpen={showAddCandidateModal}
        onClose={() => setShowAddCandidateModal(false)}
        onCandidateAdded={handleUploadSuccess}
      />

      <AddJobModal
        isOpen={showAddJobModal}
        onClose={() => setShowAddJobModal(false)}
        onJobCreated={handleJobCreated}
      />

      <JobDetailModal
        isOpen={selectedJob !== null}
        job={selectedJob}
        onClose={() => setSelectedJob(null)}
        onJobUpdated={handleJobUpdated}
        onJobDeleted={handleDeleteJob}
      />
    </div>
  );
}

export default App;
