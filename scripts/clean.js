#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

function removeDir(dir) {
  if (!fs.existsSync(dir)) return;
  
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.lstatSync(filePath);
    
    if (stat.isDirectory()) {
      removeDir(filePath);
    } else {
      fs.unlinkSync(filePath);
    }
  }
  fs.rmdirSync(dir);
}

console.log('Cleaning build artifacts...');

// Remove frontend build
const frontendNext = path.join(__dirname, '..', 'apps', 'frontend', '.next');
if (fs.existsSync(frontendNext)) {
  console.log('  Removing apps/frontend/.next');
  removeDir(frontendNext);
}

// Remove Python cache (optional)
const backendCache = path.join(__dirname, '..', 'apps', 'backend', '__pycache__');
if (fs.existsSync(backendCache)) {
  console.log('  Removing apps/backend/__pycache__');
  removeDir(backendCache);
}

const pytestCache = path.join(__dirname, '..', 'apps', 'backend', '.pytest_cache');
if (fs.existsSync(pytestCache)) {
  console.log('  Removing apps/backend/.pytest_cache');
  removeDir(pytestCache);
}

console.log('Clean complete!');

