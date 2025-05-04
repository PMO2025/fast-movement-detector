import React, { useState } from 'react';
import './App.css';
import UploadWindow from './components/UploadWindow';
import PreviewWindow from './components/PreviewWindow';
import LoadingWindow from './components/LoadingWindow';
import ResultsWindow from './components/ResultsWindow';
import {uploadVideo,
        checkStatus,
        downloadVideo} from './api.js';

function App() {
  const [currentStep, setCurrentStep] = useState('upload');
  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [processedVideoUrl, setProcessedVideoUrl] = useState('');
  const [error, setError] = useState(null);

  const handleUpload = (file) => {
    setVideoFile(file);
    setVideoUrl(URL.createObjectURL(file));
    setCurrentStep('preview');
  };

  const handleInfer = async () => {
    try {
      setCurrentStep('loading');
      const response = await uploadVideo(videoFile);
      setTaskId(response.id);
      
      checkStatus(response.id, (data) => {
        if (data.status === 'pending') {
          setProgress(data.progress * 100);
        } else if (data.status === 'complete') {
          setCurrentStep('results');
        } else if (data.status === 'error') {
          setError(data.error);
        }
      });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDownload = async () => {
    try {
      const blob = await downloadVideo(taskId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `processed_${videoFile.name}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReset = () => {
    setCurrentStep('upload');
    setVideoFile(null);
    setVideoUrl('');
    setTaskId(null);
    setProgress(0);
    setProcessedVideoUrl('');
    setError(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Детектор резкого ускорения в кадре</h1>
      </header>
      
      <main className="app-main">
        {error && (
          <div className="error-message">
            <p>{error}</p>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}
        
        {currentStep === 'upload' && (
          <UploadWindow onUpload={handleUpload} />
        )}
        
        {currentStep === 'preview' && (
          <PreviewWindow videoUrl={videoUrl} onInfer={handleInfer} onBack={handleReset} />
        )}
        
        {currentStep === 'loading' && (
          <LoadingWindow progress={progress} />
        )}
        
        {currentStep === 'results' && (
          <ResultsWindow 
            videoUrl={processedVideoUrl} 
            onDownload={handleDownload} 
            onReset={handleReset} 
          />
        )}
      </main>
      
      <footer className="app-footer">
        <p>ИИР НГУ © {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}

export default App;