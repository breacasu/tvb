import React, { useState, useEffect } from 'react';
import './LogViewer.css';

function LogViewer() {
  const [logs, setLogs] = useState([]);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    if (window.electronAPI) {
      const result = await window.electronAPI.readLogs();
      if (result.error) {
        console.error('Failed to load logs:', result.error);
        return;
      }
      // Parse log content: each line is a log entry
      const lines = result.content.split('\n').filter(line => line.trim());
      const parsedLogs = lines.map(line => {
        // Try to parse log format: "2026-05-15 17:30:00 - INFO - message"
        const match = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+-\s+(\w+)\s+-\s+(.*)$/);
        if (match) {
          return {
            timestamp: match[1],
            level: match[2],
            message: match[3]
          };
        } else {
          return {
            timestamp: '',
            level: 'INFO',
            message: line
          };
        }
      });
      setLogs(parsedLogs);
    } else {
      // Fallback sample logs for development
      const sampleLogs = [
        { timestamp: '2026-05-15 17:30:00', level: 'INFO', message: 'Starting TVB version 1.0.1' },
        { timestamp: '2026-05-15 17:30:01', level: 'DEBUG', message: 'Loading configuration...' },
        { timestamp: '2026-05-15 17:30:02', level: 'INFO', message: 'Processing file: movie1.mkv' }
      ];
      setLogs(sampleLogs);
    }
  };

  const handleClear = async () => {
    if (window.electronAPI) {
      await window.electronAPI.clearLogs();
      setLogs([]);
    }
  };

  const getLevelClass = (level) => {
    switch(level) {
      case 'ERROR': return 'error';
      case 'WARNING': return 'warning';
      case 'INFO': return 'info';
      default: return 'debug';
    }
  };

  return (
    <div className="log-viewer">
      <h3>Log Viewer</h3>
      <div className="log-controls">
        <button onClick={handleClear}>Clear Logs</button>
        <label>
          <input type="checkbox" checked={autoScroll} onChange={e => setAutoScroll(e.target.checked)} />
          Auto-scroll
        </label>
      </div>
      <div className="log-entries">
        {logs.map((log, idx) => (
          <div key={idx} className={`log-entry ${getLevelClass(log.level)}`}>
            <span className="timestamp">{log.timestamp}</span>
            <span className="level">{log.level}</span>
            <span className="message">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LogViewer;
