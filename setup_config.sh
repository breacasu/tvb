#!/bin/bash

# TVB - Setup Personal Configuration
# Copies example config to personal config if it doesn't exist

set -e

CONFIG_FILE="tvb-config.ini"
EXAMPLE_FILE="tvb-config.ini.example"

echo "🎯 TVB Configuration Setup"
echo "==========================="

if [[ -f "$CONFIG_FILE" ]]; then
    echo "✅ Personal config already exists: $CONFIG_FILE"
    echo "💡 Edit it manually or delete it to recreate from example"
    exit 0
fi

if [[ ! -f "$EXAMPLE_FILE" ]]; then
    echo "❌ Example config not found: $EXAMPLE_FILE"
    echo "💡 Make sure you're in the correct directory"
    exit 1
fi

echo "📋 Copying example config to personal config..."
cp "$EXAMPLE_FILE" "$CONFIG_FILE"

echo "✅ Personal config created: $CONFIG_FILE"
echo ""
echo "📝 Next steps:"
echo "1. Edit $CONFIG_FILE with your personal settings"
echo "2. Adjust inputdir and outputdir paths"
echo "3. Enable optional features if needed (preserve_atmos_audio, cpulimit, etc.)"
echo ""
echo "🚀 Ready to use TVB!"
