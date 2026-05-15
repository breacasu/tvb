const { app, BrowserWindow, dialog } = require('electron');
const ipcMain = require('electron').ipcMain || require('electron').default?.ipcMain;
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    icon: path.join(__dirname, '../assets/icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Load the React app or static HTML
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers using ipcMain.on()
ipcMain.on('transcode:start', (event, options) => {
  const { input, output, format, preview, hibernate, mux, dryRun, backend } = options;
  
  const args = ['tvb.py', '-i', input];
  if (output) args.push('-o', output);
  if (format) args.push('-f', format);
  if (preview) args.push('-P');
  if (hibernate) args.push('-H');
  if (mux) args.push('-m');
  if (dryRun) args.push('-d');
  if (backend && backend !== 'auto') args.push('--backend', backend);
  
  const pythonPath = path.join(__dirname, '../python');  
  
  pythonProcess = spawn('python3', args, {
    cwd: pythonPath,
    env: { ...process.env, TVB_CONFIG_PATH: path.join(app.getPath('userData'), 'tvb-config.ini') }
  });

  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString();
    try {
      const json = JSON.parse(output.trim());
      mainWindow.webContents.send('transcode:progress', json);
    } catch (e) {
      mainWindow.webContents.send('transcode:log', output);
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    mainWindow.webContents.send('transcode:error', data.toString());
  });

  pythonProcess.on('close', (code) => {
    mainWindow.webContents.send('transcode:complete', { code });
    pythonProcess = null;
  });

  event.returnValue = { started: true };
});

ipcMain.on('transcode:stop', (event) => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
  event.returnValue = { stopped: true };
});

ipcMain.on('config:read', (event) => {
  const configPath = path.join(app.getPath('userData'), 'tvb-config.ini');
  try {
    const content = fs.readFileSync(configPath, 'utf-8');
    event.returnValue = { content };
  } catch (e) {
    event.returnValue = { error: e.message };
  }
});

ipcMain.on('config:write', (event, content) => {
  const configPath = path.join(app.getPath('userData'), 'tvb-config.ini');
  fs.writeFileSync(configPath, content, 'utf-8');
  event.returnValue = { success: true };
});

ipcMain.on('stats:read', (event) => {
  const statsPath = path.join(process.cwd(), 'tvb-stats.csv');
  try {
    const content = fs.readFileSync(statsPath, 'utf-8');
    event.returnValue = { content };
  } catch (e) {
    event.returnValue = { error: e.message };
  }
});

ipcMain.on('logs:read', (event) => {
  const logPath = path.join(process.cwd(), 'transcode.log');
  try {
    const content = fs.readFileSync(logPath, 'utf-8');
    event.returnValue = { content };
  } catch (e) {
    event.returnValue = { error: e.message };
  }
});

ipcMain.on('logs:clear', (event) => {
  const logPath = path.join(process.cwd(), 'transcode.log');
  try {
    fs.writeFileSync(logPath, '', 'utf-8');
    event.returnValue = { success: true };
  } catch (e) {
    event.returnValue = { error: e.message };
  }
});

ipcMain.on('dialog:openFile', (event) => {
  dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [{ name: 'Video', extensions: ['mp4', 'mkv', 'avi', 'mov', 'm4v'] }]
  }).then(result => {
    event.returnValue = result;
  });
});

ipcMain.on('dialog:openDirectory', (event) => {
  dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  }).then(result => {
    event.returnValue = result;
  });
});

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
