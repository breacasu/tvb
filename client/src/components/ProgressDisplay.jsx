import React from 'react';
import './ProgressDisplay.css';

function ProgressDisplay({ progress, currentFile, totalFiles, fileName, fileProgress, eta }) {
  return (
    <div className="progress-display">
      <div className="batch-progress">
        <span className="progress-label">Batch</span>
        <div className="progress-bar-container">
          <div className="progress-bar-fill" style={{ width: progress + '%' }} />
          <span className="progress-text">{progress.toFixed(1)}%</span>
        </div>
        <span className="file-counter">
          File {currentFile || 0} of {totalFiles || 0}
          {eta && <span className="eta"> — ETA {eta}</span>}
        </span>
      </div>

      {fileName && (
        <div className="file-progress">
          <span className="progress-label">{fileName}</span>
          <div className="progress-bar-container">
            <div className="progress-bar-fill file-progress-fill" style={{ width: fileProgress + '%' }} />
            <span className="progress-text">{fileProgress.toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProgressDisplay;