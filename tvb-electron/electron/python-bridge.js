/**
 * Python Bridge - Replaces sys.platform checks from tvb.py
 * Uses process.platform for OS-specific logic
 */

const { platform } = require('os');
const path = require('path');
const fs = require('fs');

class PythonBridge {
  constructor() {
    this.platform = platform();
    this.toolPaths = this._detectTools();
  }

  /**
   * Get typical tool paths based on OS
   */
  getTypicalPaths() {
    const paths = {
      darwin: [ // macOS
        '/opt/homebrew/bin',
        '/usr/local/bin',
        '/usr/bin',
        '/opt/homebrew/opt/ruby/bin',
        '/usr/local/opt/ruby/bin'
      ],
      win32: [ // Windows
        'C:\\bin',
        'C:\\Program Files\\HandBrake',
        'C:\\Program Files\\HandBrake Nightly',
        'C:\\Program Files (x86)\\HandBrake',
        'C:\\Program Files\\MKVToolNix',
        'C:\\Program Files (x86)\\MKVToolNix',
        'C:\\Ruby34-x64\\bin',
        'C:\\Ruby26-x64\\bin',
        'C:\\Ruby25-x64\\bin'
      ],
      linux: [ // Linux
        '/usr/bin',
        '/usr/local/bin',
        '/opt/bin',
        '/snap/bin'
      ]
    };
    return paths[this.platform] || [];
  }

  /**
   * Find tool by name - replaces find_tool() from tvb.py
   */
  findTool(toolName, configSection = null) {
    const platformPaths = this.getTypicalPaths();
    
    // 1. Check PATH using 'which' equivalent
    // In Electron, this would be handled by the main process
    
    // 2. Search in typical paths
    for (const basePath of platformPaths) {
      const toolPath = path.join(basePath, toolName);
      if (fs.existsSync(toolPath)) {
        return toolPath;
      }
      
      // Check for .exe on Windows
      if (this.platform === 'win32') {
        const exePath = toolPath + '.exe';
        if (fs.existsSync(exePath)) return exePath;
      }
    }
    
    return null;
  }

  /**
   * Find Ruby executable - replaces find_ruby_executable() from tvb.py
   */
  findRubyExecutable(scriptPath = null) {
    const platformPaths = this.getTypicalPaths();
    
    // 1. Check same directory as script
    if (scriptPath) {
      const scriptDir = path.dirname(scriptPath);
      const rubyName = this.platform === 'win32' ? 'ruby.exe' : 'ruby';
      const rubyPath = path.join(scriptDir, rubyName);
      if (fs.existsSync(rubyPath)) return rubyPath;
    }
    
    // 2. Check typical paths
    for (const basePath of platformPaths) {
      const rubyName = this.platform === 'win32' ? 'ruby.exe' : 'ruby';
      const rubyPath = path.join(basePath, rubyName);
      if (fs.existsSync(rubyPath)) return rubyPath;
    }
    
    return null;
  }

  /**
   * Detect all required tools - replaces multiple calls in tvb.py
   */
  _detectTools() {
    return {
      handbrakeCLI: this.findTool('HandBrakeCLI'),
      mkvmerge: this.findTool('mkvmerge'),
      mkvpropedit: this.findTool('mkvpropedit'),
      ruby: this.findRubyExecutable(),
      transcodeVideo: this.findTool('transcode-video.rb') || this.findTool('transcode-video')
    };
  }

  /**
   * Get platform-specific command arguments
   */
  getPlatformArgs() {
    return {
      platform: this.platform,
      isWindows: this.platform === 'win32',
      isMac: this.platform === 'darwin',
      isLinux: this.platform === 'linux'
    };
  }

  /**
   * Hibernate command based on OS
   */
  getHibernateCommand() {
    if (this.platform === 'darwin') {
      return 'pmset sleepnow';
    } else if (this.platform === 'win32') {
      return '%windir%\\system32\\rundll32.exe powrprof.dll,SetSuspendState Hibernate';
    } else if (this.platform === 'linux') {
      return 'systemctl suspend'; // or similar
    }
    return null;
  }

  /**
   * Clean path for platform - replaces clean_path_for_platform() from tvb.py
   */
  cleanPath(pathStr) {
    if (this.platform === 'win32') {
      return pathStr; // Keep backslashes
    } else {
      return pathStr.replace(/\\/g, ''); // Remove backslash escapes
    }
  }

  /**
   * Quote path if needed - replaces quote_path_if_needed() from tvb.py
   */
  quotePath(pathStr) {
    if (pathStr.includes(' ') && !pathStr.startsWith('"')) {
      return `"${pathStr}"`;
    }
    return pathStr;
  }
}

module.exports = PythonBridge;
