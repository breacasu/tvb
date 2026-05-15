const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Transcode controls
  startTranscode: (options) => ipcRenderer.invoke('transcode:start', options),
  stopTranscode: () => ipcRenderer.invoke('transcode:stop'),
  
  // Progress listeners
  onProgress: (callback) => ipcRenderer.on('transcode:progress', callback),
  onLog: (callback) => ipcRenderer.on('transcode:log', callback),
  onError: (callback) => ipcRenderer.on('transcode:error', callback),
  onComplete: (callback) => ipcRenderer.on('transcode:complete', callback),
  
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
  
  // Remove listeners
  removeAllListeners: () => {
    ipcRenderer.removeAllListeners('transcode:progress');
    ipcRenderer.removeAllListeners('transcode:log');
    ipcRenderer.removeAllListeners('transcode:error');
    ipcRenderer.removeAllListeners('transcode:complete');
  }
});
