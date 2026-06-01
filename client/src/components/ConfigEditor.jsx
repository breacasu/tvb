import React, { useState, useEffect } from 'react';
import './ConfigEditor.css';

function ConfigEditor({ onConfigSaved }) {
  const [config, setConfig] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    if (window.electronAPI) {
      const result = await window.electronAPI.readConfig();
      if (result.content) {
        setConfig(result.content);
      }
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    if (window.electronAPI) {
      await window.electronAPI.writeConfig(config);
      if (onConfigSaved) onConfigSaved(config);
    }
    setIsSaving(false);
  };

  return (
    <div className="config-editor">
      <textarea
        value={config}
        onChange={e => setConfig(e.target.value)}
        rows={20}
        cols={80}
      />
      <button onClick={handleSave} disabled={isSaving}>
        {isSaving ? 'Saving...' : 'Save Config'}
      </button>
    </div>
  );
}

export default ConfigEditor;
