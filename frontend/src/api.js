const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function apiCall(endpoint, body) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok || data.success === false) {
    const message = data.error || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data.data;
}

export const endpoints = {
  summarize: '/api/summarize',
  ask: '/api/ask',
  generate: '/api/generate',
  analyze: '/api/analyze',
  suggest: '/api/suggest',
};
