@echo off
REM TVB - Setup Personal Configuration (Windows)
REM Copies example config to personal config if it doesn't exist

echo 🎯 TVB Configuration Setup
echo ===========================

if exist "tvb-config.ini" (
    echo ✅ Personal config already exists: tvb-config.ini
    echo 💡 Edit it manually or delete it to recreate from example
    goto :end
)

if not exist "tvb-config.ini.example" (
    echo ❌ Example config not found: tvb-config.ini.example
    echo 💡 Make sure you're in the correct directory
    goto :error
)

echo 📋 Copying example config to personal config...
copy "tvb-config.ini.example" "tvb-config.ini"

if errorlevel 1 (
    echo ❌ Failed to copy config file
    goto :error
)

echo ✅ Personal config created: tvb-config.ini
echo.
echo 📝 Next steps:
echo 1. Edit tvb-config.ini with your personal settings
echo 2. Adjust inputdir and outputdir paths
echo 3. Enable optional features if needed (preserve_atmos_audio, cpulimit, etc.)
echo.
echo 🚀 Ready to use TVB!

goto :end

:error
echo ❌ Setup failed!
exit /b 1

:end
