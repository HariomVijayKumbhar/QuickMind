const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getAuthHeaders() {
  try {
    const stored = localStorage.getItem('qm_token');
    if (stored) {
      return { Authorization: `Bearer ${stored}` };
    }
  } catch {}
  return {};
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('qm_token', token);
  } else {
    localStorage.removeItem('qm_token');
  }
}

async function handleResponse(response) {
  if (response.status === 401) {
    localStorage.removeItem('qm_token');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok || data.success === false) {
    const message = data.error || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data;
}

export async function apiCall(endpoint, body, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
    body: body ? JSON.stringify(body) : undefined,
    ...options,
  });

  const data = await handleResponse(response);
  return data.data;
}

export async function uploadFile(file) {
  const url = `${API_BASE}/api/upload`;
  const form = new FormData();
  form.append('file', file);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
    body: form,
  });

  const data = await handleResponse(response);
  return data.data;
}

export async function analyzeImage(file) {
  const url = `${API_BASE}/api/vision`;
  const form = new FormData();
  form.append('file', file);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
    body: form,
  });

  const data = await handleResponse(response);
  return data.data;
}

export const endpoints = {
  summarize: '/api/summarize',
  ask: '/api/ask',
  generate: '/api/generate',
  analyze: '/api/analyze',
  suggest: '/api/suggest',
};
