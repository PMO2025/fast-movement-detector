import React, { useCallback, useState, useRef } from 'react';

const UploadWindow = ({ onUpload }) => {
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState('');
  const fileInputRef = useRef(null);

  const handleBrowseClick = () => {
    fileInputRef.current.click();
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.size > 300 * 1024 * 1024) {
        setFileError('Превышен лимит в 300 MB.');
        return;
      }
      if (!file.type.includes('video/')) {
        setFileError('Загрузите видеоролик, а не это вот ваше...');
        return;
      }
      setFileError('');
      onUpload(file);
    }
  }, [onUpload]);

  const handleChange = useCallback((e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 300 * 1024 * 1024) {
        setFileError('Превышен лимит в 300 MB.');
        return;
      }
      if (!file.type.includes('video/')) {
        setFileError('Загрузите видеоролик, а не это вот ваше...');
        return;
      }
      setFileError('');
      onUpload(file);
    }
  }, [onUpload]);

  return (
    <div className="upload-window">
      <h2>Загрузите ваше видео</h2>
      <p>Максимальный размер файла: 300 MB</p>
      
      <div 
        className={`upload-area ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          id="video-upload" 
          accept="video/*" 
          onChange={handleChange}
          ref={fileInputRef}
          style={{ display: 'none' }}
        />
        <label htmlFor="video-upload" className="upload-label">
          {dragActive ? (
            <p>Переместите видео в данное поле</p>
          ) : (
            <>
              <p>Переместите видео сюда или</p>
              <button 
                type="button" 
                className="browse-button"
                onClick={handleBrowseClick}
              >
                Найдите его в Проводнике
              </button>
            </>
          )}
        </label>
      </div>
      
      {fileError && <p className="error-text">{fileError}</p>}
    </div>
  );
};

export default UploadWindow;