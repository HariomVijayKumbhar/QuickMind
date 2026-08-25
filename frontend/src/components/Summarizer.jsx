import { useState } from 'react';
import { endpoints, apiCall } from '../api';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function Summarizer() {
  const [text, setText] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setOutput('');
    if (!text.trim()) {
      setError('Please enter some text to summarize.');
      return;
    }
    if (text.length > 8000) {
      setError('Text must be 8000 characters or fewer.');
      return;
    }
    setLoading(true);
    try {
      const result = await apiCall(endpoints.summarize, { text });
      setOutput(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="feature">
      <h2>Text Summarization</h2>
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste long text here..."
          rows={8}
          maxLength={8000}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Summarizing...' : 'Summarize'}
        </button>
      </form>
      {loading && <Loader />}
      {output && (
        <div className="output">
          <h3>Summary</h3>
          <p>{output}</p>
        </div>
      )}
    </div>
  );
}
