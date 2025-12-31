const fs = require('fs');
const path = require('path');

// Read .env file from backend directory
function loadEnvFile(filePath) {
  const env = {};
  
  if (fs.existsSync(filePath)) {
    const envContent = fs.readFileSync(filePath, 'utf8');
    envContent.split('\n').forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key && valueParts.length > 0) {
          env[key.trim()] = valueParts.join('=').trim();
        }
      }
    });
  }
  
  return env;
}

// Load environment files
const backendEnvPath = path.join(__dirname, 'apps', 'backend', '.env');
const frontendEnvPath = path.join(__dirname, 'apps', 'frontend', '.env.local');
const backendEnv = loadEnvFile(backendEnvPath);
const frontendEnv = loadEnvFile(frontendEnvPath);

module.exports = {
  apps: [
    {
      name: "chatbot-backend",
      cwd: path.join(__dirname, "apps", "backend"),
      // Use system Python if venv doesn't exist (for Windows compatibility)
      script: (() => {
        const venvPython = path.join(__dirname, "apps", "backend", "venv", process.platform === "win32" ? "Scripts" : "bin", "python" + (process.platform === "win32" ? ".exe" : ""));
        if (fs.existsSync(venvPython)) {
          return venvPython;
        }
        return process.platform === "win32" ? "python" : "python3";
      })(),
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      exec_mode: "fork",
      env: {
        ENV: "production",
        DATABASE_URL: backendEnv.DATABASE_URL || process.env.DATABASE_URL || "sqlite:///./chatbot.db",
        OPENAI_API_KEY: backendEnv.OPENAI_API_KEY || process.env.OPENAI_API_KEY || "",
        SESSION_SECRET: backendEnv.SESSION_SECRET || process.env.SESSION_SECRET || "change-me-in-production",
        FRONTEND_ORIGIN: backendEnv.FRONTEND_ORIGIN || process.env.FRONTEND_ORIGIN || "http://localhost:3000",
        MAX_CRAWL_PAGES: backendEnv.MAX_CRAWL_PAGES || process.env.MAX_CRAWL_PAGES || "100",
        CRAWL_TIMEOUT_SECONDS: backendEnv.CRAWL_TIMEOUT_SECONDS || process.env.CRAWL_TIMEOUT_SECONDS || "10",
      },
      error_file: path.join(__dirname, "logs", "backend-error.log"),
      out_file: path.join(__dirname, "logs", "backend-out.log"),
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      instances: 1,
      min_uptime: "10s",
      max_restarts: 10,
    },
    {
      name: "chatbot-frontend",
      cwd: path.join(__dirname, "apps", "frontend"),
      // Check if build exists, if not, build first
      script: (() => {
        const buildDir = path.join(__dirname, "apps", "frontend", ".next");
        if (!fs.existsSync(buildDir)) {
          console.warn("⚠️  Frontend build not found. Run 'npm run build' in apps/frontend first!");
        }
        return process.platform === "win32" ? "npm.cmd" : "npm";
      })(),
      args: "start",
      interpreter: "none",
      exec_mode: "fork",
      env: {
        NODE_ENV: "production",
        // BACKEND_URL is used by Next.js rewrite rule to proxy /api/* to backend
        // In production with nginx, this is not needed (nginx handles it)
        // In local development, this points to the backend server
        BACKEND_URL: process.env.BACKEND_URL || "http://localhost:8000",
        PORT: process.env.FRONTEND_PORT || "3000",
      },
      error_file: path.join(__dirname, "logs", "frontend-error.log"),
      out_file: path.join(__dirname, "logs", "frontend-out.log"),
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      instances: 1,
      min_uptime: "10s",
      max_restarts: 10,
    },
  ],
}
