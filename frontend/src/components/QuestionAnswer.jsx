import { useState, useEffect, useRef } from 'react';
import { endpoints, apiCall } from '../api';
import { useDocument } from '../context/DocumentContext';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function QuestionAnswer() {
  const { document, uploadDocument, isUploading } = useDocument();
  const [question, setQuestion] = useState('');
  const [context, setContext] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showContextInput, setShowContextInput] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (document?.text) {
      setContext(document.text);
    }
  }, [document]);

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
    const effectiveContext = context.trim() || document?.text || '';
    if (effectiveContext.length > 30000) {
      setError('Context must be 30000 characters or fewer.');
      return;
    }
    setLoading(true);
    try {
      const result = await apiCall(endpoints.ask, { question, context: effectiveContext });
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
    uploadDocument(file)
      .then((extracted) => {
        setContext(extracted);
      })
      .catch((err) => {
        setError(err.message);
      });
  }

  return (
    <div className="feature">
      <div className="feature-header-row">
        <h2>Document Question Answering</h2>
        {document && (
          <button
            type="button"
            className="btn-pill"
            onClick={() => setShowContextInput(!showContextInput)}
          >
            {showContextInput ? 'Hide Context Box' : 'View / Edit Context'}
          </button>
        )}
      </div>

      {document ? (
        <div className="tool-doc-badge">
          <span>📄 Questioning against: <strong>{document.name}</strong> ({document.text.length.toLocaleString()} chars)</span>
          <span className="grounding-tag">Strict Grounding: File Only</span>
        </div>
      ) : (
        <div className="tool-doc-badge">
          <span>💡 Tip: Upload a document above or click below to ask questions strictly from your file.</span>
        </div>
      )}

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={document ? `Ask any question about ${document.name}...` : "Ask any question..."}
          maxLength={2000}
        />

        {(!document || showContextInput) && (
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Optional context or paste document text here..."
            rows={4}
            maxLength={30000}
          />
        )}

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
            {loading ? 'Searching Document & Answering...' : 'Ask Question'}
          </button>
        </div>
      </form>

      {loading && <Loader />}
      {output && (
        <div className="output">
          <div className="output-header">
            <h3>Answer</h3>
            <span className="output-source-badge">Grounding: Based strictly on document content</span>
          </div>
          <p>{output}</p>
        </div>
      )}
    </div>
  );
}
