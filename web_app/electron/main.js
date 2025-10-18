const { app, BrowserWindow, shell, dialog } = require('electron');
const path = require('path');

const isDev = !!process.env.VITE_DEV_SERVER_URL;

const createMainWindow = () => {
  const window = new BrowserWindow({
    width: 1280,
    height: 768,
    minWidth: 960,
    minHeight: 600,
    backgroundColor: '#f6f7fb',
    title: 'Florería Carlitos',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  window.removeMenu();

  if (isDev) {
    window.loadURL(process.env.VITE_DEV_SERVER_URL);
    window.webContents.openDevTools({ mode: 'detach' });
  } else {
    const indexPath = path.join(app.getAppPath(), 'dist', 'index.html');
    window.loadFile(indexPath).catch((error) => {
      dialog.showErrorBox('No se pudo iniciar la interfaz', error.message);
    });
  }

  window.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
};

app.whenReady().then(() => {
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
