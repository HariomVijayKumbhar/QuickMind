import { useState } from 'react';
import { endpoints, apiCall } from '../api';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function DocumentAnalyzer() {
  const [text, setText] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setOutput('');
    if (!text.trim()) {
      setError('Please paste or upload a document.');
      return;
    }
    if (text.length > 8000) {
      setError('Document must be 8000 characters or fewer.');
      return;
    }
    setLoading(true);
    try {
      const result = await apiCall(endpoints.analyze, { text });
      setOutput(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="feature">
      <h2>Text / Document Analysis</h2>
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste or type your document here..."
          rows={10}
          maxLength={8000}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </form>
      {loading && <Loader />}
      {output && (
        <div className="output">
          <h3>Analysis</h3>
          <p>{output}</p>
        </div>
      )}
    </div>
  );
}
