import { useState, useRef } from 'react';
import { endpoints, apiCall } from '../api';
import { useDocument } from '../context/DocumentContext';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function SuggestionEngine() {
  const { document, uploadDocument, isUploading } = useDocument();
  const [task, setTask] = useState('');
  const [useDocContext, setUseDocContext] = useState(true);
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

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
      const payload = {
        task,
        context: (useDocContext && document?.text) ? document.text : '',
      };
      const result = await apiCall(endpoints.suggest, payload);
      setOutput(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    uploadDocument(file).catch((err) => setError(err.message));
  }

  return (
    <div className="feature">
      <div className="feature-header-row">
        <h2>Intelligent Suggestions & Recommendations</h2>
      </div>

      {document ? (
        <div className="tool-doc-badge">
          <label className="context-toggle-label">
            <input
              type="checkbox"
              checked={useDocContext}
              onChange={(e) => setUseDocContext(e.target.checked)}
            />
            <span>Base suggestions on: <strong>{document.name}</strong></span>
          </label>
          {useDocContext && <span className="grounding-tag">Strict Grounding: File Only</span>}
        </div>
      ) : (
        <div className="tool-doc-badge">
          <span>💡 Tip: Upload a file to get strategic next steps and recommendations grounded strictly in your document.</span>
        </div>
      )}

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit}>
        <input
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder={
            document && useDocContext
              ? `What advice or next steps do you need regarding ${document.name}? (e.g. 'Identify critical risk factors and mitigation steps')`
              : "Describe your task or goal (e.g. 'Plan a sprint retrospective')..."
          }
          maxLength={2000}
        />

        <div className="form-actions-row">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
            onChange={handleFileUpload}
            hidden
          />
          <button
            type="button"
            className="btn-upload-secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading || isUploading}
          >
            {isUploading ? 'Extracting File...' : '📁 Upload Document'}
          </button>

          <button type="submit" className="btn-primary" disabled={loading || isUploading}>
            {loading ? 'Generating Suggestions...' : 'Get Suggestions'}
          </button>
        </div>
      </form>

      {loading && <Loader />}
      {output && (
        <div className="output">
          <div className="output-header">
            <h3>Strategic Recommendations</h3>
            {document && useDocContext && (
              <span className="output-source-badge">Derived strictly from {document.name}</span>
            )}
          </div>
          <p>{output}</p>
        </div>
      )}
    </div>
  );
}
