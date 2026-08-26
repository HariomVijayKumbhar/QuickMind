import { createContext, useContext, useState } from 'react';
import { uploadFile } from '../api';

const DocumentContext = createContext(null);

export const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'image/png',
  'image/jpeg',
];

export function DocumentProvider({ children }) {
  const [document, setDocument] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  async function uploadDocument(file) {
    if (!file) return;
    setUploadError('');

    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File size must be under 10MB.');
      return;
    }

    setIsUploading(true);
    try {
      const extractedText = await uploadFile(file);
      if (!extractedText || !extractedText.trim()) {
        throw new Error('No text could be extracted from this file.');
      }
      const formattedSize = file.size < 1024 * 1024
        ? `${(file.size / 1024).toFixed(1)} KB`
        : `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

      setDocument({
        name: file.name,
        size: formattedSize,
        text: extractedText,
      });
      setUploadError('');
      return extractedText;
    } catch (err) {
      setUploadError(err.message || 'Failed to process file.');
      throw err;
    } finally {
      setIsUploading(false);
    }
  }

  function clearDocument() {
    setDocument(null);
    setUploadError('');
  }

  function updateDocumentText(newText) {
    if (!document) {
      setDocument({
        name: 'Manual Input Document',
        size: `${(new Blob([newText]).size / 1024).toFixed(1)} KB`,
        text: newText,
      });
    } else {
      setDocument({
        ...document,
        text: newText,
        size: `${(new Blob([newText]).size / 1024).toFixed(1)} KB`,
      });
    }
  }

  return (
    <DocumentContext.Provider
      value={{
        document,
        setDocument,
        uploadDocument,
        clearDocument,
        updateDocumentText,
        isUploading,
        uploadError,
        setUploadError,
      }}
    >
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocument() {
  const ctx = useContext(DocumentContext);
  if (!ctx) {
    throw new Error('useDocument must be used within a DocumentProvider');
  }
  return ctx;
}
