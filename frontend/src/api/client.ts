// API client for communicating with the FastAPI backend

// Use Vite env variable, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function uploadResume(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/candidates/upload-resume`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
}

export async function getCandidates() {
    const response = await fetch(`${API_BASE_URL}/candidates/`);
    if (!response.ok) {
        throw new Error(`Failed to fetch candidates: ${response.statusText}`);
    }
    return response.json();
}

export async function getCandidate(candidateId: string) {
    const response = await fetch(`${API_BASE_URL}/candidates/${candidateId}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch candidate: ${response.statusText}`);
    }
    return response.json();
}

export async function createJob(job: {
    title: string;
    description: string;
    required_skills: string[];
    preferred_skills?: string[];
    company?: string;
    location?: string;
}) {
    const response = await fetch(`${API_BASE_URL}/candidates/jobs`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(job),
    });

    if (!response.ok) {
        throw new Error(`Failed to create job: ${response.statusText}`);
    }

    return response.json();
}

export async function getJobs() {
    const response = await fetch(`${API_BASE_URL}/candidates/jobs/`);
    if (!response.ok) {
        throw new Error(`Failed to fetch jobs: ${response.statusText}`);
    }
    return response.json();
}

export async function generateQuestions(candidateId: string, jobId: string) {
    const response = await fetch(
        `${API_BASE_URL}/candidates/generate-questions?candidate_id=${candidateId}&job_id=${jobId}`,
        {
            method: 'POST',
        }
    );

    if (!response.ok) {
        throw new Error(`Failed to generate questions: ${response.statusText}`);
    }

    return response.json();
}

export async function initiateCall(
    candidateId: string,
    jobId: string,
    agentId?: string,
    agentPhoneNumberId?: string,
    phoneOverride?: string
) {
    const response = await fetch(`${API_BASE_URL}/candidates/initiate-call`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            candidate_id: candidateId,
            job_id: jobId,
            agent_id: agentId,
            agent_phone_number_id: agentPhoneNumberId,
            phone_override: phoneOverride,
        }),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to initiate call: ${response.statusText}`);
    }

    return response.json();
}

export async function getCallStatus(callId: string) {
    const response = await fetch(`${API_BASE_URL}/candidates/calls/${callId}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch call status: ${response.statusText}`);
    }
    return response.json();
}

export async function getCallDetails(callId: string) {
    const response = await fetch(`${API_BASE_URL}/candidates/calls/${callId}/details`);
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch call details: ${response.statusText}`);
    }
    return response.json();
}

export async function deleteCandidate(candidateId: string) {
    const response = await fetch(`${API_BASE_URL}/candidates/${candidateId}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete candidate: ${response.statusText}`);
    }
    return response.json();
}

export async function deleteJob(jobId: string) {
    const response = await fetch(`${API_BASE_URL}/candidates/jobs/${jobId}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete job: ${response.statusText}`);
    }
    return response.json();
}

export async function updateJob(jobId: string, job: {
    title: string;
    description: string;
    required_skills: string[];
    preferred_skills?: string[];
    company?: string;
    location?: string;
}) {
    const response = await fetch(`${API_BASE_URL}/candidates/jobs/${jobId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...job, id: jobId }),
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to update job: ${response.statusText}`);
    }
    return response.json();
}



