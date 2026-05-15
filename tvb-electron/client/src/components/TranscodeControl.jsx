import React, { useState } from 'react';
import './TranscodeControl.css';

function TranscodeControl() {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [format, setFormat] = useState('');
  const [preview, setPreview] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  const handleStart = async () => {
    if (!input) return;
    setIsRunning(true);
    if (window.electronAPI) {
      const options = {
        input,
        output,
        format,
        preview,
        hibernate: false,
        mux: false,
        dryRun: false,
        backend: 'auto'
      };
      await window.electronAPI.startTranscode(options);
    }
  };

  const handleStop = async () => {
    if (window.electronAPI) {
      await window.electronAPI.stopTranscode();
    }
    setIsRunning(false);
  };

  const handleSelectInput = async () => {
    if (window.electronAPI) {
      const result = await window.electronAPI.openFile();
      if (result && !result.canceled && result.filePaths) {
        setInput(result.filePaths[0]);
      }
    }
  };

  return (
    <div className="transcode-control">
      <h2>Transcode Video Batch</h2>
      <div className="control-group">
        <label>Input: </label>
        <input type="text" value={input} onChange={e => setInput(e.target.value)} />
        <button onClick={handleSelectInput}>Browse...</button>
      </div>
      <div className="control-group">
        <label>Output: </label>
        <input type="text" value={output} onChange={e => setOutput(e.target.value)} />
      </div>
      <div className="control-group">
        <label>Format: </label>
        <select value={format} onChange={e => setFormat(e.target.value)}>
          <option value="">Auto-detect</option>
          <option value="movie">Movie</option>
          <option value="tvshow">TV Show</option>
          <option value="custom">Custom</option>
        </select>
      </div>
      <div className="control-group">
        <label>
          <input type="checkbox" checked={preview} onChange={e => setPreview(e.target.checked)} />
          Preview (30s)
        </label>
      </div>
      <div className="button-group">
        {!isRunning ? (
          <button onClick={handleStart}>Start Transcoding</button>
        ) : (
          <button onClick={handleStop}>Stop</button>
        )}
      </div>
    </div>
  );
}

export default TranscodeControl;
