const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('floreria', {
  version: process.versions.electron,
});
