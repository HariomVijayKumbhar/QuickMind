import { useState, useRef } from 'react';
import { useDocument } from '../context/DocumentContext';

export default function DocumentBanner() {
  const { document, uploadDocument, clearDocument, isUploading, uploadError } = useDocument();
  const [showPreview, setShowPreview] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  function handleFileSelected(file) {
    if (!file) return;
    uploadDocument(file).catch(() => {});
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  }

  return (
    <div className="global-doc-wrapper">
      {uploadError && <div className="error-banner">{uploadError}</div>}

      {!document ? (
        <div
          className={`global-upload-zone ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <div className="upload-zone-content">
            <span className="upload-icon">📄</span>
            <div className="upload-text">
              <strong>Upload a Document</strong>
              <p>PDF, DOCX, TXT, PNG, JPG (up to 10MB) • Shared across Summarize, Ask, Generate, Analyze & Suggest</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
              onChange={(e) => handleFileSelected(e.target.files[0])}
              hidden
            />
            <button
              type="button"
              className="btn-upload"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              {isUploading ? 'Extracting Text...' : 'Choose File'}
            </button>
          </div>
        </div>
      ) : (
        <div className="active-doc-card">
          <div className="active-doc-header">
            <div className="active-doc-left">
              <span className="active-doc-icon">📑</span>
              <div>
                <div className="active-doc-title-row">
                  <span className="active-doc-name">{document.name}</span>
                  <span className="active-doc-badge">Active in All Tools</span>
                </div>
                <div className="active-doc-meta">
                  <span>{document.size}</span>
                  <span>•</span>
                  <span>{document.text.length.toLocaleString()} characters</span>
                  <span>•</span>
                  <span>Grounding enabled (answers strictly from file)</span>
                </div>
              </div>
            </div>
            <div className="active-doc-actions">
              <button
                type="button"
                className="btn-secondary-sm"
                onClick={() => setShowPreview(!showPreview)}
              >
                {showPreview ? 'Hide Text' : 'Preview Text'}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
                onChange={(e) => handleFileSelected(e.target.files[0])}
                hidden
              />
              <button
                type="button"
                className="btn-secondary-sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
              >
                {isUploading ? 'Uploading...' : 'Replace'}
              </button>
              <button
                type="button"
                className="btn-danger-sm"
                onClick={() => {
                  clearDocument();
                  setShowPreview(false);
                }}
              >
                Remove
              </button>
            </div>
          </div>

          {showPreview && (
            <div className="active-doc-preview">
              <div className="preview-header">
                <span>Extracted Document Content ({document.text.length} chars)</span>
              </div>
              <textarea
                className="preview-textarea"
                value={document.text}
                readOnly
                rows={6}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
