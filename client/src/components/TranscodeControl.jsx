import React, { useState } from 'react';
import './TranscodeControl.css';

function TranscodeControl({ previewDuration, isRunning, onStart, onStartRejected, onStopped }) {
  const [input, setInput] = useState([]);
  const [inputLabel, setInputLabel] = useState('');
  const [output, setOutput] = useState('');
  const [format, setFormat] = useState('');
  const [preview, setPreview] = useState(false);
  const [atmos, setAtmos] = useState(true);
  const [dryRun, setDryRun] = useState(false);
  const handleStart = async () => {
    if (!input || input.length === 0) return;
    if (onStart) onStart();
    if (window.electronAPI) {
      try {
        const result = await window.electronAPI.startTranscode({
          input, output, format: format || undefined,
          preview, dryRun, atmos,
        });
        if (result && result.started === false) {
          if (onStartRejected) onStartRejected(result.error || 'Could not start transcoding');
        }
      } catch (error) {
        if (onStartRejected) onStartRejected(String(error));
      }
    } else if (onStartRejected) {
      onStartRejected('Electron API is not available');
    }
  };

  const handleStop = async () => {
    if (window.electronAPI) {
      await window.electronAPI.stopTranscode();
    }
    if (onStopped) onStopped();
  };

  const handleSelectInput = async () => {
    if (window.electronAPI) {
      const result = await window.electronAPI.openFile();
      if (result && !result.canceled && result.filePaths && result.filePaths.length > 0) {
        setInput(result.filePaths);
        if (result.filePaths.length === 1) {
          setInputLabel(result.filePaths[0]);
        } else {
          setInputLabel(`${result.filePaths.length} files selected`);
        }
      }
    }
  };

  const handleSelectOutput = async () => {
    if (window.electronAPI) {
      const result = await window.electronAPI.openDirectory();
      if (result && !result.canceled && result.filePaths) {
        setOutput(result.filePaths[0]);
      }
    }
  };

  return (
    <div className="transcode-control">
      <div className="control-group">
        <label>Input:</label>
        <input type="text" value={inputLabel} onChange={e => { setInputLabel(e.target.value); setInput(e.target.value ? [e.target.value] : []); }} placeholder="Video file(s) or directory" />
        <button onClick={handleSelectInput}>Browse...</button>
      </div>

      <div className="control-group">
        <label>Output:</label>
        <input type="text" value={output} onChange={e => setOutput(e.target.value)} placeholder="Output directory" />
        <button onClick={handleSelectOutput}>Browse...</button>
      </div>

      <div className="control-group">
        <label>Format:</label>
        <select value={format} onChange={e => setFormat(e.target.value)}>
          <option value="">Auto-detect</option>
          <option value="movie">Movie</option>
          <option value="tvshow">TV Show</option>
          <option value="custom">Custom</option>
        </select>
      </div>

      <div className="toggles">
        <label>
          <input type="checkbox" checked={preview} onChange={e => setPreview(e.target.checked)} />
          Preview ({previewDuration >= 60 ? `${Math.round(previewDuration / 60)}min` : `${previewDuration}s`})
        </label>
        <label>
          <input type="checkbox" checked={atmos} onChange={e => setAtmos(e.target.checked)} />
          Preserve Atmos
        </label>
        <label>
          <input type="checkbox" checked={dryRun} onChange={e => setDryRun(e.target.checked)} />
          Dry-run
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
