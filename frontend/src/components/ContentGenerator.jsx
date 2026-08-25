import { useState } from 'react';
import { endpoints, apiCall } from '../api';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function ContentGenerator() {
  const [prompt, setPrompt] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setOutput('');
    if (!prompt.trim()) {
      setError('Please enter a prompt.');
      return;
    }
    if (prompt.length > 2000) {
      setError('Prompt must be 2000 characters or fewer.');
      return;
    }
    setLoading(true);
    try {
      const result = await apiCall(endpoints.generate, { prompt });
      setOutput(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="feature">
      <h2>Content Generation</h2>
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit}>
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe what you want to generate..."
          maxLength={2000}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Generating...' : 'Generate'}
        </button>
      </form>
      {loading && <Loader />}
      {output && (
        <div className="output">
          <h3>Generated Content</h3>
          <p>{output}</p>
        </div>
      )}
    </div>
  );
}
