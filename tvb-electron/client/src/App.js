import React, { useState, useEffect } from 'react';
import TranscodeControl from './components/TranscodeControl';
import ProgressDisplay from './components/ProgressDisplay';
import StatsDashboard from './components/StatsDashboard';
import LogViewer from './components/LogViewer';
import ConfigEditor from './components/ConfigEditor';
import './index.css';

function App() {
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [fileName, setFileName] = useState('');
  const [fileProgress, setFileProgress] = useState(0);

  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.onProgress((event, data) => {
        if (data.type === 'progress') {
          setProgress(data.progress || 0);
          setCurrentFile(data.current || 0);
          setTotalFiles(data.total || 0);
          setFileName(data.filename || '');
          setFileProgress(data.progress || 0);
        }
      });

      window.electronAPI.onComplete((event, data) => {
        console.log('Transcoding complete:', data);
      });
    }
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>TVB - Transcode Video Batch</h1>
      </header>
      <main>
        <div className="dashboard">
          <TranscodeControl />
          <ProgressDisplay 
            progress={progress}
            currentFile={currentFile}
            totalFiles={totalFiles}
            fileName={fileName}
            fileProgress={fileProgress}
          />
        </div>
        <StatsDashboard />
        <LogViewer />
        <ConfigEditor />
      </main>
    </div>
  );
}

export default App;
