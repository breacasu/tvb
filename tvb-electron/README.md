# TVB Electron App

Transcode Video Batch - Electron Edition

## Features
- Cross-platform GUI (macOS, Windows, Linux)
- Batch video transcoding
- Dolby Atmos preservation
- Multiple backend support (Ruby/Python)
- Progress tracking and statistics

## Development

```bash
# Install dependencies
npm install

# Start React dev server
cd src && npm start

# In another terminal, start Electron
npm start
```

## Building

```bash
# Build for current platform
npm run build

# Build for specific platforms
npm run build:mac
npm run build:win
npm run build:linux
```

## Migration Status

- [x] Project structure created
- [x] Electron main process setup
- [x] Python backend copied
- [ ] React UI components (in progress)
- [ ] Full integration testing
- [ ] Remove old OS-specific wrappers
