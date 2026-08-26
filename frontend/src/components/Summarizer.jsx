import { useState, useEffect, useRef } from 'react';
import { endpoints, apiCall } from '../api';
import { useDocument } from '../context/DocumentContext';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function Summarizer() {
  const { document, uploadDocument, isUploading } = useDocument();
  const [text, setText] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  // Auto-fill from active document if local text is empty
  useEffect(() => {
    if (document?.text && !text) {
      setText(document.text);
    }
  }, [document]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setOutput('');
    const targetText = text.trim() || document?.text || '';
    if (!targetText) {
      setError('Please paste text or upload a document to summarize.');
      return;
    }
    if (targetText.length > 30000) {
      setError('Text must be 30000 characters or fewer.');
      return;
    }
    setLoading(true);
    try {
      const result = await apiCall(endpoints.summarize, { text: targetText });
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
        setText(extracted);
      })
      .catch((err) => {
        setError(err.message);
      });
  }

  return (
    <div className="feature">
      <div className="feature-header-row">
        <h2>Detailed Document Summarization</h2>
        {document && (
          <button
            type="button"
            className="btn-pill"
            onClick={() => setText(document.text)}
            title="Reset text area to active document"
          >
            📋 Use "{document.name}"
          </button>
        )}
      </div>

      {document && (
        <div className="tool-doc-badge">
          <span>📄 Active Document: <strong>{document.name}</strong> ({document.text.length.toLocaleString()} chars)</span>
          <span className="grounding-tag">Strict Grounding: File Only</span>
        </div>
      )}

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={document ? `Using content from ${document.name}...` : "Paste long text or upload a document..."}
          rows={8}
          maxLength={30000}
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
            {isUploading ? 'Extracting File...' : '📁 Upload New File'}
          </button>

          <button type="submit" className="btn-primary" disabled={loading || isUploading}>
            {loading ? 'Generating Detailed Summary...' : 'Summarize Document'}
          </button>
        </div>
      </form>

      {loading && <Loader />}
      {output && (
        <div className="output">
          <div className="output-header">
            <h3>Detailed Summary</h3>
            <span className="output-source-badge">Derived strictly from document</span>
          </div>
          <p>{output}</p>
        </div>
      )}
    </div>
  );
}
