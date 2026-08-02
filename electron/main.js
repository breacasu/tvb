const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const fs = require('fs');

process.on('uncaughtException', (err) => {
  console.error('Uncaught exception:', err);
});

let mainWindow = null;
let pythonProcess = null;
let processSummary = null;

function sendToRenderer(channel, data) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send(channel, data);
  }
}

function getResourcePath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'app');
  }
  return path.join(__dirname, '..');
}

function getPythonBin() {
  const resourcePath = getResourcePath();
  if (app.isPackaged) {
    const isWin = process.platform === 'win32';
    const exe = isWin ? 'tvb.exe' : 'tvb';
    const bundled = path.join(resourcePath, 'python', 'dist', exe);
    if (fs.existsSync(bundled)) return bundled;
    throw new Error(`Bundled tvb CLI not found: ${bundled}`);
  }
  return process.platform === 'win32' ? 'python' : 'python3';
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
  return path.join(getDataDir(), 'tvb-config.ini');
}

function getDataDir() {
  if (process.env.TVB_DATA_DIR) return process.env.TVB_DATA_DIR;
  const home = app.getPath('home');
  const candidates = [
    path.join(home, 'SynologyDrive', 'SharedRepoDocuments', 'tvb'),
    path.join(home, 'Synology Drive', 'SharedRepoDocuments', 'tvb'),
  ];
  const shared = candidates.find((candidate) => fs.existsSync(candidate));
  return shared || app.getPath('userData');
}

function stopPythonProcess() {
  if (!pythonProcess) return;
  if (process.platform === 'win32' && pythonProcess.pid) {
    spawn('taskkill', ['/pid', String(pythonProcess.pid), '/t', '/f'], {
      windowsHide: true,
      stdio: 'ignore',
    });
  } else {
    pythonProcess.kill('SIGTERM');
  }
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
  if (isDev && process.argv.includes('--dev')) {
    mainWindow.loadURL('http://localhost:5173').catch(() => {
      mainWindow.loadFile(path.join(__dirname, '../client/dist/index.html'));
    });
  } else {
    mainWindow.loadFile(path.join(__dirname, '../client/dist/index.html'));
  }

  mainWindow.on('closed', () => { mainWindow = null; });

  mainWindow.webContents.on('did-fail-load', (_event, code, desc) => {
    console.error(`Render process load failed: ${code} - ${desc}`);
  });
}

app.whenReady().then(() => {
  ipcMain.handle('transcode:start', async (_event, options) => {
    if (pythonProcess) {
      return { started: false, error: 'A transcode job is already running' };
    }

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
    args.push(atmos === false ? '--no-preserve-atmos' : '--preserve-atmos');
    args.push('--debug');

    processSummary = null;
    try {
      pythonProcess = spawn(getPythonBin(), args, {
        cwd: getPythonCwd(),
        windowsHide: true,
        env: {
          ...process.env,
          TVB_CONFIG_PATH: getTvbConfigPath(),
          TVB_DATA_DIR: getDataDir(),
          TVB_TOOLS_DIR: app.isPackaged
            ? path.join(getResourcePath(), 'tools')
            : (process.env.TVB_TOOLS_DIR || ''),
          TVB_BUNDLED_ONLY: app.isPackaged ? '1' : (process.env.TVB_BUNDLED_ONLY || '0'),
        },
      });
    } catch (error) {
      sendToRenderer('transcode:error', String(error));
      return { started: false, error: String(error) };
    }

    let stdoutBuffer = '';
    const handleLine = (line) => {
      const trimmed = line.trim();
      if (!trimmed) return;
      try {
        const json = JSON.parse(trimmed);
        if (json.type === 'log') {
          sendToRenderer('transcode:log', {
            timestamp: json.timestamp || '',
            level: json.level || 'INFO',
            message: json.message || '',
          });
        } else if (json.type === 'progress') {
          sendToRenderer('transcode:progress', json);
        } else if (json.type === 'error') {
          sendToRenderer('transcode:error', json.message || 'Transcode failed');
        } else if (json.type === 'complete') {
          processSummary = json;
        } else if (json.type === 'file_complete') {
          sendToRenderer('transcode:progress', {
            current: json.current,
            total: json.total,
            progress: json.progress,
            filename: json.filename,
            filePercent: 100,
            eta: '',
          });
        } else {
          sendToRenderer('transcode:log', {
            timestamp: '', level: 'INFO', message: JSON.stringify(json),
          });
        }
      } catch {
        sendToRenderer('transcode:log', {
          timestamp: '', level: 'INFO', message: trimmed,
        });
      }
    };

    pythonProcess.stdout.on('data', (data) => {
      stdoutBuffer += data.toString();
      const lines = stdoutBuffer.split(/\r?\n/);
      stdoutBuffer = lines.pop() || '';
      lines.forEach(handleLine);
    });

    pythonProcess.stderr.on('data', (data) => {
      sendToRenderer('transcode:log', {
        timestamp: '', level: 'ERROR', message: data.toString().trim(),
      });
    });

    pythonProcess.on('error', (error) => {
      sendToRenderer('transcode:error', String(error));
    });

    pythonProcess.on('close', (code) => {
      if (stdoutBuffer.trim()) handleLine(stdoutBuffer);
      sendToRenderer('transcode:complete', {
        ...(processSummary || {}),
        code,
        success: code === 0,
      });
      pythonProcess = null;
      processSummary = null;
    });

    return { started: true };
  });

  ipcMain.handle('transcode:stop', async () => {
    stopPythonProcess();
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

  ipcMain.handle('stats:read', async () => {
    const statsPath = path.join(getDataDir(), 'tvb-stats.csv');
    try { return { content: fs.readFileSync(statsPath, 'utf-8') }; }
    catch { return { error: 'No stats file found' }; }
  });

  ipcMain.handle('logs:read', async () => {
    const logPath = path.join(getDataDir(), 'transcode.log');
    try { return { content: fs.readFileSync(logPath, 'utf-8') }; }
    catch { return { error: 'No log file found' }; }
  });

  ipcMain.handle('logs:clear', async () => {
    const logPath = path.join(getDataDir(), 'transcode.log');
    try { fs.writeFileSync(logPath, '', 'utf-8'); return { success: true }; }
    catch { return { error: 'Cannot clear log' }; }
  });

  ipcMain.handle('dialog:openFile', async () => {
    return await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile', 'openDirectory', 'multiSelections'],
      filters: [{ name: 'Videos', extensions: ['mp4', 'mkv', 'avi', 'mov', 'm4v', 'flv', 'mpg', 'mpeg', 'wmv'] }],
    });
  });

  ipcMain.handle('dialog:openDirectory', async () => {
    return await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
    });
  });

  function findTool(name) {
    const isWin = process.platform === 'win32';
    const exe = isWin ? `${name}.exe` : name;
    const bundled = path.join(getResourcePath(), 'bin', exe);
    if (fs.existsSync(bundled)) return bundled;
    try {
      const cmd = isWin ? `where ${exe}` : `which ${name}`;
      const result = execSync(cmd, { stdio: ['pipe', 'pipe', 'ignore'] }).toString().trim();
      return result.split(/\r?\n/)[0] || '';
    } catch {
      return '';
    }
  }

  ipcMain.handle('tools:detect', async () => {
    return {
      tools: {
        handbrake: findTool('HandBrakeCLI'),
        ffprobe: findTool('ffprobe'),
      },
    };
  });

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  stopPythonProcess();
});
