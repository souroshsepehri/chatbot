module.exports = {
  apps: [
    {
      name: "chatbot-backend",
      cwd: "./apps/backend",
      interpreter: "./apps/backend/.venv/bin/python",
      script: "-m",
      args: "uvicorn app.main:app --host 127.0.0.1 --port 8000",
      exec_mode: "fork",
      env: {
        ENV: "production",
      },
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
    },
    {
      name: "chatbot-frontend",
      cwd: "./apps/frontend",
      script: "npm",
      args: "run start -- -p 3000",
      exec_mode: "fork",
      env: {
        NODE_ENV: "production",
      },
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
    },
  ],
}
