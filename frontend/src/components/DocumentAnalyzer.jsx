import { useState, useEffect, useRef } from 'react';
import { endpoints, apiCall } from '../api';
import { useDocument } from '../context/DocumentContext';
import Loader from './Loader';
import ErrorBanner from './ErrorBanner';

export default function DocumentAnalyzer() {
  const { document, uploadDocument, isUploading } = useDocument();
  const [text, setText] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

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
      setError('Please paste or upload a document to analyze.');
      return;
    }
    if (targetText.length > 30000) {
      setError('Document must be 30000 characters or fewer.');
      return;
    }
    setLoading(true);
    try {
      const result = await apiCall(endpoints.analyze, { text: targetText });
      setOutput(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleFileChange(e) {
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
        <h2>In-Depth Document Analysis</h2>
        {document && (
          <button
            type="button"
            className="btn-pill"
            onClick={() => setText(document.text)}
            title="Reset to active document text"
          >
            📋 Use "{document.name}"
          </button>
        )}
      </div>

      {document ? (
        <div className="tool-doc-badge">
          <span>📄 Analyzing: <strong>{document.name}</strong> ({document.text.length.toLocaleString()} chars)</span>
          <span className="grounding-tag">Strict Grounding: File Only</span>
        </div>
      ) : (
        <div className="tool-doc-badge">
          <span>💡 Upload any PDF, DOCX, TXT, or Image to perform a complete in-depth analysis.</span>
        </div>
      )}

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={document ? `Analyzing content from ${document.name}...` : "Paste or type your document here..."}
          rows={9}
          maxLength={30000}
        />

        <div className="form-actions-row">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
            onChange={handleFileChange}
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
            {loading ? 'Performing In-Depth Analysis...' : 'Analyze Document'}
          </button>
        </div>
      </form>

      {loading && <Loader />}
      {output && (
        <div className="output">
          <div className="output-header">
            <h3>Document Analysis Report</h3>
            <span className="output-source-badge">Strict Evidence-Based Analysis</span>
          </div>
          <p>{output}</p>
        </div>
      )}
    </div>
  );
}
