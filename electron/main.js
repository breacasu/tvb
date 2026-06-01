const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const fs = require('fs');

let mainWindow = null;
let pythonProcess = null;

function getResourcePath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'app');
  }
  return path.join(__dirname, '..');
}

function getPythonBin() {
  const resourcePath = getResourcePath();
  if (app.isPackaged) {
    const bundled = path.join(resourcePath, 'python', 'dist', 'tvb');
    if (fs.existsSync(bundled)) return bundled;
  }
  return 'python3';
}

function getPythonArgs() {
  if (app.isPackaged) {
    return [];
  }
  return ['-u', 'tvb.py'];
}

function getPythonDir() {
  if (app.isPackaged) {
    return path.join(getResourcePath(), 'python');
  }
  return path.join(__dirname, '..', 'python');
}

function getPythonCwd() {
  return getPythonDir();
}

function getTvbConfigPath() {
  return path.join(app.getPath('userData'), 'tvb-config.ini');
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const isDev = !app.isPackaged;
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173').catch(() => {
      mainWindow.loadFile(path.join(__dirname, '../client/dist/index.html'));
    });
  } else {
    mainWindow.loadFile(path.join(__dirname, '../client/dist/index.html'));
  }

  mainWindow.on('closed', () => { mainWindow = null; });
}

app.whenReady().then(() => {
  ipcMain.handle('transcode:start', async (_event, options) => {
    const { input, output, format, preview, dryRun, atmos } = options || {};

    const inputs = Array.isArray(input) ? input : [input];
    let args = [...getPythonArgs()];
    for (const inp of inputs) {
      args.push('-i', inp);
    }

    if (output) args.push('-o', output);
    if (format) args.push('-f', format);
    if (preview) args.push('-P');
    if (dryRun) args.push('-d');
    args.push('--debug');

    pythonProcess = spawn(getPythonBin(), args, {
      cwd: getPythonCwd(),
      env: {
        ...process.env,
        TVB_CONFIG_PATH: getTvbConfigPath(),
      },
    });

    pythonProcess.stdout.on('data', (data) => {
      const lines = data.toString().split('\n').filter(l => l.trim());
      for (const line of lines) {
        try {
          const json = JSON.parse(line.trim());
          if (json.type === 'log') {
            mainWindow.webContents.send('transcode:log', {
              timestamp: json.timestamp || '',
              level: json.level || 'INFO',
              message: json.message || '',
            });
          } else if (json.type === 'progress') {
            mainWindow.webContents.send('transcode:progress', {
              current: json.current,
              total: json.total,
              progress: json.progress,
              filename: json.filename,
              filePercent: json.filePercent,
              eta: json.eta,
            });
          } else if (json.type === 'error') {
            mainWindow.webContents.send('transcode:error', json.message);
          } else if (json.type === 'complete') {
            mainWindow.webContents.send('transcode:complete', json);
          } else if (json.type === 'file_complete') {
            mainWindow.webContents.send('transcode:progress', {
              current: null, total: null, progress: 100,
              filename: json.filename, filePercent: 100, eta: '',
            });
          } else {
            mainWindow.webContents.send('transcode:log', {
              timestamp: '', level: 'INFO',
              message: JSON.stringify(json),
            });
          }
        } catch {
          mainWindow.webContents.send('transcode:log', {
            timestamp: '', level: 'INFO', message: line,
          });
        }
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      mainWindow.webContents.send('transcode:error', data.toString());
    });

    pythonProcess.on('close', (code) => {
      mainWindow.webContents.send('transcode:complete', { code, success: code === 0 });
      pythonProcess = null;
    });

    return { started: true };
  });

  ipcMain.handle('transcode:stop', async () => {
    if (pythonProcess) {
      pythonProcess.kill();
      pythonProcess = null;
    }
    return { stopped: true };
  });

  ipcMain.handle('config:read', async () => {
    const configPath = getTvbConfigPath();
    try { return { content: fs.readFileSync(configPath, 'utf-8') }; } catch {
      try {
        return { content: fs.readFileSync(path.join(getResourcePath(), 'python', 'tvb-config.ini'), 'utf-8') };
      } catch { return { error: 'No config file found' }; }
    }
  });

  ipcMain.handle('config:write', async (_event, content) => {
    const configPath = getTvbConfigPath();
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(configPath, content, 'utf-8');
    return { success: true };
  });

  const projectRoot = getResourcePath();
  ipcMain.handle('stats:read', async () => {
    const statsPath = path.join(projectRoot, 'python', 'tvb-stats.csv');
    try { return { content: fs.readFileSync(statsPath, 'utf-8') }; }
    catch { return { error: 'No stats file found' }; }
  });

  ipcMain.handle('logs:read', async () => {
    const logPath = path.join(projectRoot, 'python', 'transcode.log');
    try { return { content: fs.readFileSync(logPath, 'utf-8') }; }
    catch { return { error: 'No log file found' }; }
  });

  ipcMain.handle('logs:clear', async () => {
    const logPath = path.join(projectRoot, 'python', 'transcode.log');
    try { fs.writeFileSync(logPath, '', 'utf-8'); return { success: true }; }
    catch { return { error: 'Cannot clear log' }; }
  });

  ipcMain.handle('dialog:openFile', async () => {
    return await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile', 'openDirectory', 'multiSelections'],
      filters: [{ name: 'Videos', extensions: ['mp4', 'mkv', 'avi', 'mov', 'm4v'] }],
    });
  });

  ipcMain.handle('dialog:openDirectory', async () => {
    return await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
    });
  });

  ipcMain.handle('tools:detect', async () => {
    const tools = {};
    try {
      tools.handbrake = execSync('which HandBrakeCLI 2>/dev/null || echo ""').toString().trim();
      tools.ffmpeg = execSync('which ffprobe 2>/dev/null || echo ""').toString().trim();
    } catch {}
    return { tools };
  });

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});