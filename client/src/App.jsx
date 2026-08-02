import React, { useState, useEffect } from 'react';
import TranscodeControl from './components/TranscodeControl';
import ProgressDisplay from './components/ProgressDisplay';
import StatsDashboard from './components/StatsDashboard';
import LogViewer from './components/LogViewer';
import ConfigEditor from './components/ConfigEditor';
import CollapsibleSection from './components/CollapsibleSection';
import './index.css';

function App() {
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [fileName, setFileName] = useState('');
  const [fileProgress, setFileProgress] = useState(0);
  const [eta, setEta] = useState('');
  const [statsKey, setStatsKey] = useState(0);
  const [logs, setLogs] = useState([]);
  const [previewDuration, setPreviewDuration] = useState(30);
  const [isRunning, setIsRunning] = useState(false);

  const appendLog = (entry) => {
    setLogs(prev => [...prev, {
      timestamp: entry.timestamp || '',
      level: entry.level || 'INFO',
      message: entry.message || '',
    }]);
  };

  const parseLogLine = (line) => {
    const trimmed = line.trim();
    if (!trimmed) return null;
    const match = trimmed.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+-\s+(\w+)\s+-\s+(.*)$/);
    return match
      ? { timestamp: match[1], level: match[2], message: match[3] }
      : { timestamp: '', level: 'INFO', message: trimmed };
  };

  useEffect(() => {
    if (!window.electronAPI) return;

    const unsubProgress = window.electronAPI.onProgress((data) => {
      if (!data) return;

      if (data.progress != null) setProgress(data.progress);
      if (data.current != null) setCurrentFile(data.current);
      if (data.total != null) setTotalFiles(data.total);
      if (data.filename) setFileName(data.filename);
      if (data.filePercent != null) setFileProgress(data.filePercent);
      if (data.eta) setEta(data.eta);
    });

    const unsubLog = window.electronAPI.onLog((data) => {
      if (!data) return;
      if (typeof data === 'object') {
        appendLog(data);
      } else {
        const parsed = parseLogLine(data);
        if (parsed) appendLog(parsed);
      }
    });

    const unsubError = window.electronAPI.onError((message) => {
      appendLog({ level: 'ERROR', message: String(message || 'Transcode failed') });
    });

    const unsubComplete = window.electronAPI.onComplete((data) => {
      setIsRunning(false);
      setProgress(100);
      setFileProgress(100);
      if (data && data.success === false) {
        appendLog({ level: 'ERROR', message: `Transcode failed (exit code ${data.code ?? 'unknown'})` });
      }
      // Force StatsDashboard to remount and reload the csv
      setStatsKey(k => k + 1);
    });

    window.electronAPI.readLogs().then((result) => {
      if (!result?.content) return;
      const loaded = result.content.split(/\r?\n/).map(parseLogLine).filter(Boolean);
      setLogs(loaded);
    });

    return () => {
      unsubProgress();
      unsubLog();
      unsubError();
      unsubComplete();
    };
  }, []);

  const handleClearLogs = () => {
    setLogs([]);
  };

  const handleConfigSaved = (configText) => {
    const match = configText.match(/\[preview\][\s\S]*?parameter\s*=\s*.*?duration:(\d+)/);
    if (match) {
      setPreviewDuration(parseInt(match[1], 10));
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>TVB</h1>
      </header>
      <main>
        <TranscodeControl
          previewDuration={previewDuration}
          isRunning={isRunning}
          onStart={() => {
            setIsRunning(true);
            setProgress(0);
            setFileProgress(0);
            setCurrentFile(0);
            setTotalFiles(0);
            setFileName('');
            setEta('');
          }}
          onStartRejected={(message) => {
            setIsRunning(false);
            appendLog({ level: 'ERROR', message });
          }}
          onStopped={() => setIsRunning(false)}
        />
        <ProgressDisplay
          progress={progress}
          currentFile={currentFile}
          totalFiles={totalFiles}
          fileName={fileName}
          fileProgress={fileProgress}
          eta={eta}
        />
        <CollapsibleSection title="Stats" defaultOpen={false}>
          <StatsDashboard key={statsKey} />
        </CollapsibleSection>
        <CollapsibleSection title="Log" defaultOpen={false}>
          <LogViewer logs={logs} onClear={handleClearLogs} />
        </CollapsibleSection>
        <CollapsibleSection title="Config" defaultOpen={false}>
          <ConfigEditor onConfigSaved={handleConfigSaved} onConfigLoaded={handleConfigSaved} />
        </CollapsibleSection>
      </main>
    </div>
  );
}

export default App;
