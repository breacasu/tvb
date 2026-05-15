import React from 'react';
import './ProgressDisplay.css';

function ProgressDisplay({ progress, currentFile, totalFiles, fileName, fileProgress }) {
  const batchStyle = { width: progress + '%' };
  const fileStyle = { width: fileProgress + '%' };

  return (
    <div className="progress-display">
      <h3>Transcoding Progress</h3>
      
      <div className="batch-progress">
        <label>Batch Progress:</label>
        <div className="progress-bar-container">
          <div className="progress-bar-fill" style={batchStyle}></div>
          <span className="progress-text">{progress.toFixed(1)}%</span>
        </div>
        <span className="file-counter">File {currentFile} of {totalFiles}</span>
      </div>

      {fileName && (
        <div className="file-progress">
          <label>Current File: {fileName}</label>
          <div className="progress-bar-container">
            <div className="progress-bar-fill file-progress-fill" style={fileStyle}></div>
            <span className="progress-text">{fileProgress.toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProgressDisplay;
