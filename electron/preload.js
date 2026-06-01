const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Transcode controls
  startTranscode: (options) => ipcRenderer.invoke('transcode:start', options),
  stopTranscode: () => ipcRenderer.invoke('transcode:stop'),

  // Progress listeners — return unsubscribe functions
  onProgress: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('transcode:progress', handler);
    return () => ipcRenderer.removeListener('transcode:progress', handler);
  },
  onLog: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('transcode:log', handler);
    return () => ipcRenderer.removeListener('transcode:log', handler);
  },
  onError: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('transcode:error', handler);
    return () => ipcRenderer.removeListener('transcode:error', handler);
  },
  onComplete: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('transcode:complete', handler);
    return () => ipcRenderer.removeListener('transcode:complete', handler);
  },

  // Reload triggers for stats/logs after complete
  reloadStats: () => { ipcRenderer.emit('transcode:reload-stats'); },
  reloadLogs: () => { ipcRenderer.emit('transcode:reload-logs'); },

  // Config management
  readConfig: () => ipcRenderer.invoke('config:read'),
  writeConfig: (content) => ipcRenderer.invoke('config:write', content),

  // Stats & Logs
  readStats: () => ipcRenderer.invoke('stats:read'),
  readLogs: () => ipcRenderer.invoke('logs:read'),
  clearLogs: () => ipcRenderer.invoke('logs:clear'),

  // Tool detection
  detectTools: () => ipcRenderer.invoke('tools:detect'),

  // Dialog helpers
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  openDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),

  // Clean up all listener refs
  removeAllListeners: (channels) => {
    const chans = channels || ['transcode:progress', 'transcode:log', 'transcode:error', 'transcode:complete'];
    chans.forEach((ch) => ipcRenderer.removeAllListeners(ch));
  },
});
