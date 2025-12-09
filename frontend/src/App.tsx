import { useState, useEffect } from 'react';
import { ResumeUpload } from './components/ResumeUpload';
import { CandidateList } from './components/CandidateList';
import { JobForm } from './components/JobForm';
import { ScreeningPanel } from './components/ScreeningPanel';
import { getCandidates, getJobs } from './api/client';
import type { Candidate, JobDescription } from './types';
import './App.css';

function App() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

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
    setCandidates(prev => [...prev, candidate]);
    setSelectedCandidate(candidate);
  };

  const handleJobCreated = (job: JobDescription) => {
    setJobs(prev => [...prev, job]);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">🎯</span>
          <h1>AI Candidate Screener</h1>
        </div>
        <p className="tagline">Automated Phone Screening Powered by AI</p>
      </header>

      <main className="dashboard">
        <div className="dashboard-left">
          <ResumeUpload onUploadSuccess={handleUploadSuccess} />
          <JobForm onJobCreated={handleJobCreated} />
          <CandidateList
            candidates={candidates}
            selectedCandidate={selectedCandidate}
            onSelectCandidate={setSelectedCandidate}
          />
        </div>

        <div className="dashboard-right">
          <ScreeningPanel
            candidate={selectedCandidate}
            jobs={jobs}
          />
        </div>
      </main>

      <footer className="app-footer">
        <p>Phase 1: Resume Upload & AI Screening • Phase 2: ATS/CRM Integration (Coming Soon)</p>
      </footer>
    </div>
  );
}

export default App;
