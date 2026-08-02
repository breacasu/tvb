const fs = require('fs');
const path = require('path');

exports.default = async function (context) {
  const { appOutDir, electronPlatformName } = context;
  if (electronPlatformName !== 'win32') return;

  const batPath = path.join(appOutDir, 'tvb.bat');
  const content = `@echo off
set "TVB_CONFIG_PATH=%~dp0resources\\app\\python\\tvb-config.ini"
set "TVB_DATA_DIR=%USERPROFILE%\\SynologyDrive\\SharedRepoDocuments\\tvb"
if not exist "%TVB_DATA_DIR%" set "TVB_DATA_DIR=%LOCALAPPDATA%\\tvb"
"%~dp0resources\\app\\python\\dist\\tvb.exe" --text %*
`;
  fs.writeFileSync(batPath, content, 'utf-8');
  console.log(`[afterPack] Created: ${batPath}`);

  const staleCropBat = path.join(appOutDir, 'tvb-crop.bat');
  if (fs.existsSync(staleCropBat)) fs.unlinkSync(staleCropBat);
};
