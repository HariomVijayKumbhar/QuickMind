import { useState, useRef } from 'react';
import { endpoints, apiCall } from '../api';
import { useDocument } from '../context/DocumentContext';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function ContentGenerator() {
  const { document, uploadDocument, isUploading } = useDocument();
  const [prompt, setPrompt] = useState('');
  const [useDocContext, setUseDocContext] = useState(true);
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

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
      const payload = {
        prompt,
        context: (useDocContext && document?.text) ? document.text : '',
      };
      const result = await apiCall(endpoints.generate, payload);
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
        <h2>Content Generation</h2>
      </div>

      {document ? (
        <div className="tool-doc-badge">
          <label className="context-toggle-label">
            <input
              type="checkbox"
              checked={useDocContext}
              onChange={(e) => setUseDocContext(e.target.checked)}
            />
            <span>Use active file: <strong>{document.name}</strong> as source context</span>
          </label>
          {useDocContext && <span className="grounding-tag">Strict Grounding: File Only</span>}
        </div>
      ) : (
        <div className="tool-doc-badge">
          <span>💡 Tip: Upload a document to generate content (reports, emails, FAQs) derived strictly from it.</span>
        </div>
      )}

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit}>
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={
            document && useDocContext
              ? `What would you like to generate from ${document.name}? (e.g. 'Draft a client email summarizing key milestones')`
              : "Describe what you want to generate (e.g. 'Write a professional project update')..."
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
            {loading ? 'Generating Content...' : 'Generate Content'}
          </button>
        </div>
      </form>

      {loading && <Loader />}
      {output && (
        <div className="output">
          <div className="output-header">
            <h3>Generated Content</h3>
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
