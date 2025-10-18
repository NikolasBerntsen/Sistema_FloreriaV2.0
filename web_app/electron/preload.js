const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('floreria', {
  version: process.env.npm_package_version,
});
