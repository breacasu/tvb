import React, { useState, useEffect } from 'react';
import './LogViewer.css';

function LogViewer({ logs: externalLogs, onClear }) {
  const [internalLogs, setInternalLogs] = useState([]);
  const logs = externalLogs ?? internalLogs;
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (!externalLogs) {
      loadLogs();
    }
  }, [externalLogs]);

  useEffect(() => {
    if (!window.electronAPI || externalLogs) return;

    const unsubLog = window.electronAPI.onLog((line) => {
      if (!line || !line.trim()) return;
      const trimmed = line.trim();
      const match = trimmed.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+-\s+(\w+)\s+-\s+(.*)$/);
      const newLog = match
        ? { timestamp: match[1], level: match[2], message: match[3] }
        : { timestamp: '', level: 'INFO', message: trimmed };
      setInternalLogs(prev => [...prev, newLog]);
    });

    const unsubProgress = window.electronAPI.onProgress((data) => {
      if (data?.type === 'log') {
        setInternalLogs(prev => [...prev, {
          timestamp: '',
          level: data.level || 'INFO',
          message: data.message || ''
        }]);
      }
    });

    return () => {
      unsubLog();
      unsubProgress();
    };
  }, []);

  const loadLogs = async () => {
    if (window.electronAPI) {
      const result = await window.electronAPI.readLogs();
      if (result.error) return;
      const lines = result.content.split('\n').filter(line => line.trim());
      const parsedLogs = lines.map(line => {
        const match = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+-\s+(\w+)\s+-\s+(.*)$/);
        return match
          ? { timestamp: match[1], level: match[2], message: match[3] }
          : { timestamp: '', level: 'INFO', message: line };
      });
      setInternalLogs(parsedLogs);
    }
  };

  const handleClear = async () => {
    if (window.electronAPI) {
      await window.electronAPI.clearLogs();
      setInternalLogs([]);
      if (onClear) onClear();
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

  const scrollRef = React.useRef(null);
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  return (
    <div className="log-viewer">
      <div className="log-controls">
        <button onClick={handleClear}>Clear</button>
        <label>
          <input type="checkbox" checked={autoScroll} onChange={e => setAutoScroll(e.target.checked)} />
          Auto-scroll
        </label>
      </div>
      <div className="log-entries" ref={scrollRef}>
        {logs.map((log, idx) => (
          <div key={idx} className={`log-entry ${getLevelClass(log.level)}`}>
            {log.timestamp && <span className="timestamp">{log.timestamp}</span>}
            {log.timestamp && <span className="level">{log.level}</span>}
            <span className="message">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LogViewer;