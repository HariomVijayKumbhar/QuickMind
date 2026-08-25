import { useState } from 'react';
import { endpoints, apiCall } from '../api';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function QuestionAnswer() {
  const [question, setQuestion] = useState('');
  const [context, setContext] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setOutput('');
    if (!question.trim()) {
      setError('Please enter a question.');
      return;
    }
    if (question.length > 2000) {
      setError('Question must be 2000 characters or fewer.');
      return;
    }
    if (context.length > 8000) {
      setError('Context must be 8000 characters or fewer.');
      return;
    }
    setLoading(true);
    try {
      const result = await apiCall(endpoints.ask, { question, context });
      setOutput(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="feature">
      <h2>Question Answering</h2>
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          maxLength={2000}
        />
        <textarea
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="Optional context or document..."
          rows={4}
          maxLength={8000}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Answering...' : 'Ask'}
        </button>
      </form>
      {loading && <Loader />}
      {output && (
        <div className="output">
          <h3>Answer</h3>
          <p>{output}</p>
        </div>
      )}
    </div>
  );
}
