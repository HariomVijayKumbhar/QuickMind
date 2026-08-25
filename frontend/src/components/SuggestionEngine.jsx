import { useState } from 'react';
import { endpoints, apiCall } from '../api';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function SuggestionEngine() {
  const [task, setTask] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setOutput('');
    if (!task.trim()) {
      setError('Please describe a task or goal.');
      return;
    }
    if (task.length > 2000) {
      setError('Task description must be 2000 characters or fewer.');
      return;
    }
    setLoading(true);
    try {
      const result = await apiCall(endpoints.suggest, { task });
      setOutput(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="feature">
      <h2>Intelligent Suggestions</h2>
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit}>
        <input
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="Describe your task or goal..."
          maxLength={2000}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Generating suggestions...' : 'Get Suggestions'}
        </button>
      </form>
      {loading && <Loader />}
      {output && (
        <div className="output">
          <h3>Suggestions</h3>
          <p>{output}</p>
        </div>
      )}
    </div>
  );
}
