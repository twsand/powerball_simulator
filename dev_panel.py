#!/usr/bin/env python3
"""
Powerball Simulator - Development Panel
A web-based control panel for local development and Pi deployment.

Run this on your PC to:
- Launch the simulator locally (web-only mode)
- Push changes to Git
- SSH to Pi and pull/restart
"""

import subprocess
import os
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Configuration - UPDATE THESE FOR YOUR SETUP
CONFIG = {
    "pi_host": "192.168.0.73",
    "pi_user": "twsand",
    "pi_project_path": "~/powerball_simulator",
    "dev_panel_port": 5050,
    "git_remote": "origin",
    "git_branch": "master"
}

# Log storage
logs = []

def add_log(message, level="info"):
    """Add a log entry."""
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    }
    logs.append(entry)
    if len(logs) > 100:
        logs.pop(0)
    print(f"[{entry['time']}] [{level.upper()}] {message}")

def run_command(cmd, cwd=None, capture=True):
    """Run a shell command and return output."""
    add_log(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=capture,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            add_log(f"Success: {result.stdout[:200] if result.stdout else 'OK'}")
            return True, result.stdout
        else:
            add_log(f"Failed: {result.stderr[:200] if result.stderr else 'Unknown error'}", "error")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        add_log("Command timed out", "error")
        return False, "Command timed out"
    except Exception as e:
        add_log(f"Error: {str(e)}", "error")
        return False, str(e)

def get_project_path():
    """Get the path to the powerball_simulator directory."""
    # Check if we're in the project directory
    if os.path.exists("game_engine.py"):
        return os.getcwd()
    # Check parent
    parent = os.path.dirname(os.getcwd())
    if os.path.exists(os.path.join(parent, "game_engine.py")):
        return parent
    # Default to current directory
    return os.getcwd()

# HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Powerball Dev Panel</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f1a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #ffd700; margin-bottom: 5px; }
        .subtitle { color: #666; margin-bottom: 30px; }

        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }

        .card {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2a2a4a;
        }
        .card h2 {
            margin: 0 0 15px 0;
            color: #ffd700;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-deploy {
            background: linear-gradient(135deg, #1a1a2e 0%, #2a1a3e 100%);
            border: 2px solid #ffd700;
        }
        .card-deploy h2 {
            font-size: 1.4rem;
        }

        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin: 5px 5px 5px 0;
        }
        .btn:hover { transform: translateY(-1px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        .btn-primary { background: #ffd700; color: #1a1a2e; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-secondary { background: #444; color: white; }
        .btn-info { background: #17a2b8; color: white; }

        .btn-deploy {
            background: linear-gradient(135deg, #ffd700 0%, #ffaa00 100%);
            color: #1a1a2e;
            font-size: 18px;
            font-weight: bold;
            padding: 18px 30px;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
        }
        .btn-deploy:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 215, 0, 0.4);
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-running { background: #28a745; }
        .status-stopped { background: #dc3545; }
        .status-unknown { background: #ffc107; }

        .log-container {
            background: #0a0a15;
            border-radius: 8px;
            padding: 15px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
        }
        .log-entry { margin: 4px 0; }
        .log-time { color: #666; }
        .log-info { color: #17a2b8; }
        .log-error { color: #dc3545; }
        .log-success { color: #28a745; }

        .config-display {
            background: #0a0a15;
            border-radius: 8px;
            padding: 15px;
            font-family: monospace;
            font-size: 12px;
        }
        .config-item { margin: 5px 0; }
        .config-key { color: #ffd700; }
        .config-value { color: #17a2b8; }

        .links { margin-top: 15px; }
        .links a {
            color: #ffd700;
            text-decoration: none;
            margin-right: 20px;
        }
        .links a:hover { text-decoration: underline; }

        .full-width { grid-column: 1 / -1; }

        input[type="text"] {
            padding: 10px;
            border: 1px solid #333;
            border-radius: 6px;
            background: #0a0a15;
            color: white;
            width: 100%;
            margin-bottom: 10px;
        }

        .deploy-status {
            margin-top: 10px;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            display: none;
        }
        .deploy-status.active {
            display: block;
            background: rgba(255, 215, 0, 0.1);
            border: 1px solid #ffd700;
            color: #ffd700;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Powerball Dev Panel</h1>
        <p class="subtitle">Pi deployment control - Edit on PC, deploy to Pi</p>

        <div class="grid">
            <!-- Quick Deploy - Prominent at top -->
            <div class="card card-deploy full-width">
                <h2>Quick Deploy to Pi</h2>
                <p style="color: #aaa; font-size: 14px; margin-bottom: 15px;">
                    Commits changes, pushes to git, pulls on Pi, and restarts the app - all in one click.
                </p>
                <input type="text" id="commitMsg" placeholder="Commit message (optional - defaults to 'Deploy from dev panel')">
                <button class="btn btn-deploy" onclick="quickDeploy()" style="width: 100%;">
                    Deploy to Pi
                </button>
                <div class="deploy-status" id="deployStatus"></div>
            </div>

            <!-- Git Operations -->
            <div class="card">
                <h2>Git Operations</h2>
                <button class="btn btn-primary" onclick="gitCommitPush()">Commit & Push</button>
                <button class="btn btn-secondary" onclick="gitStatus()">Status</button>
                <button class="btn btn-secondary" onclick="gitPull()">Pull</button>
            </div>

            <!-- Pi Controls -->
            <div class="card">
                <h2>Raspberry Pi</h2>
                <div id="piStatus">
                    <span class="status-indicator status-unknown"></span>
                    Not checked
                </div>
                <div style="margin-top: 15px;">
                    <button class="btn btn-info" onclick="piPull()">Pull on Pi</button>
                    <button class="btn btn-success" onclick="piRestart()">Restart App</button>
                    <button class="btn btn-secondary" onclick="piStatus()">Check Status</button>
                </div>
                <div class="links">
                    <a href="http://{{ pi_host }}:5000" target="_blank">Pi Player Page</a>
                    <a href="http://{{ pi_host }}:5000/admin" target="_blank">Pi Admin</a>
                </div>
            </div>

            <!-- Config -->
            <div class="card">
                <h2>Configuration</h2>
                <div class="config-display">
                    <div class="config-item"><span class="config-key">Pi Host:</span> <span class="config-value">{{ pi_host }}</span></div>
                    <div class="config-item"><span class="config-key">Pi User:</span> <span class="config-value">{{ pi_user }}</span></div>
                    <div class="config-item"><span class="config-key">Pi Path:</span> <span class="config-value">{{ pi_path }}</span></div>
                </div>
            </div>

            <!-- SSH Command -->
            <div class="card">
                <h2>Custom SSH Command</h2>
                <input type="text" id="sshCmd" placeholder="Command to run on Pi">
                <button class="btn btn-secondary" onclick="runSshCmd()">Run on Pi</button>
            </div>

            <!-- Logs -->
            <div class="card full-width">
                <h2>Logs</h2>
                <div class="log-container" id="logContainer">
                    <div class="log-entry"><span class="log-time">[--:--:--]</span> Ready</div>
                </div>
                <button class="btn btn-secondary" onclick="clearLogs()" style="margin-top: 10px;">Clear Logs</button>
            </div>
        </div>
    </div>

    <script>
        const PI_HOST = '{{ pi_host }}';

        async function api(endpoint, data = {}) {
            try {
                const resp = await fetch('/api/' + endpoint, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                return await resp.json();
            } catch (e) {
                return {success: false, error: e.message};
            }
        }

        async function gitStatus() {
            await api('git_status');
            refreshLogs();
        }

        async function gitPull() {
            await api('git_pull');
            refreshLogs();
        }

        async function gitCommitPush() {
            const msg = document.getElementById('commitMsg').value || 'Update from dev panel';
            await api('git_commit_push', {message: msg});
            document.getElementById('commitMsg').value = '';
            refreshLogs();
        }

        async function piPull() {
            await api('pi_pull');
            refreshLogs();
        }

        async function piRestart() {
            await api('pi_restart');
            refreshLogs();
        }

        async function piStatus() {
            const result = await api('pi_status');
            refreshLogs();
            const el = document.getElementById('piStatus');
            if (result.output && result.output.includes('powerball')) {
                el.innerHTML = '<span class="status-indicator status-running"></span> App running';
            } else {
                el.innerHTML = '<span class="status-indicator status-stopped"></span> App not detected';
            }
        }

        async function quickDeploy() {
            const statusEl = document.getElementById('deployStatus');
            statusEl.className = 'deploy-status active';
            statusEl.textContent = 'Deploying...';

            const msg = document.getElementById('commitMsg').value || 'Deploy from dev panel';
            const result = await api('quick_deploy', {message: msg});
            document.getElementById('commitMsg').value = '';
            refreshLogs();

            if (result.success) {
                statusEl.textContent = 'Deploy complete!';
                setTimeout(() => { statusEl.className = 'deploy-status'; }, 3000);
            } else {
                statusEl.textContent = 'Deploy failed - check logs';
                statusEl.style.borderColor = '#dc3545';
                statusEl.style.color = '#dc3545';
            }
        }

        async function runSshCmd() {
            const cmd = document.getElementById('sshCmd').value;
            if (!cmd) return;
            await api('ssh_command', {command: cmd});
            refreshLogs();
        }

        async function refreshLogs() {
            const result = await api('get_logs');
            if (result.logs) {
                const container = document.getElementById('logContainer');
                container.innerHTML = result.logs.map(log =>
                    `<div class="log-entry">
                        <span class="log-time">[${log.time}]</span>
                        <span class="log-${log.level}">${escapeHtml(log.message)}</span>
                    </div>`
                ).join('');
                container.scrollTop = container.scrollHeight;
            }
        }

        function clearLogs() {
            api('clear_logs');
            document.getElementById('logContainer').innerHTML = '';
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Initial load
        refreshLogs();

        // Refresh logs periodically
        setInterval(refreshLogs, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(
        DASHBOARD_HTML,
        pi_host=CONFIG["pi_host"],
        pi_user=CONFIG["pi_user"],
        pi_path=CONFIG["pi_project_path"]
    )

@app.route('/api/git_status', methods=['POST'])
def git_status():
    project_path = get_project_path()
    success, output = run_command("git status --short", cwd=project_path)
    return jsonify({"success": success, "output": output})

@app.route('/api/git_pull', methods=['POST'])
def git_pull():
    project_path = get_project_path()
    success, output = run_command("git pull", cwd=project_path)
    return jsonify({"success": success, "output": output})

@app.route('/api/git_commit_push', methods=['POST'])
def git_commit_push():
    data = request.json or {}
    message = data.get("message", "Update from dev panel")
    project_path = get_project_path()
    
    # Add all changes
    success, _ = run_command("git add -A", cwd=project_path)
    if not success:
        return jsonify({"success": False, "error": "git add failed"})
    
    # Commit
    success, output = run_command(f'git commit -m "{message}"', cwd=project_path)
    if not success and "nothing to commit" not in output:
        return jsonify({"success": False, "error": "git commit failed"})
    
    # Push
    success, output = run_command(f"git push {CONFIG['git_remote']} {CONFIG['git_branch']}", cwd=project_path)
    return jsonify({"success": success, "output": output})

@app.route('/api/pi_pull', methods=['POST'])
def pi_pull():
    cmd = f'ssh {CONFIG["pi_user"]}@{CONFIG["pi_host"]} "cd {CONFIG["pi_project_path"]} && git pull"'
    success, output = run_command(cmd)
    return jsonify({"success": success, "output": output})

@app.route('/api/pi_restart', methods=['POST'])
def pi_restart():
    # Try to restart via screen session
    cmd = f'ssh {CONFIG["pi_user"]}@{CONFIG["pi_host"]} "screen -S powerball -X quit; cd {CONFIG["pi_project_path"]} && screen -dmS powerball bash -c \'source venv/bin/activate && python main.py\'"'
    success, output = run_command(cmd)
    if success:
        add_log("Restarted powerball in screen session", "success")
    return jsonify({"success": success, "output": output})

@app.route('/api/pi_status', methods=['POST'])
def pi_status():
    cmd = f'ssh {CONFIG["pi_user"]}@{CONFIG["pi_host"]} "screen -ls | grep powerball; ps aux | grep python | grep -v grep | head -3"'
    success, output = run_command(cmd)
    return jsonify({"success": success, "output": output})

@app.route('/api/ssh_command', methods=['POST'])
def ssh_command():
    data = request.json or {}
    command = data.get("command", "")
    if not command:
        return jsonify({"success": False, "error": "No command provided"})
    
    cmd = f'ssh {CONFIG["pi_user"]}@{CONFIG["pi_host"]} "{command}"'
    success, output = run_command(cmd)
    return jsonify({"success": success, "output": output})

@app.route('/api/quick_deploy', methods=['POST'])
def quick_deploy():
    data = request.json or {}
    message = data.get("message", "Deploy from dev panel")
    project_path = get_project_path()
    
    add_log("=== QUICK DEPLOY STARTED ===")
    
    # 1. Git add & commit
    run_command("git add -A", cwd=project_path)
    run_command(f'git commit -m "{message}"', cwd=project_path)
    
    # 2. Push
    success, _ = run_command(f"git push {CONFIG['git_remote']} {CONFIG['git_branch']}", cwd=project_path)
    if not success:
        add_log("Push failed, aborting deploy", "error")
        return jsonify({"success": False, "error": "Push failed"})
    
    # 3. Pull on Pi
    cmd = f'ssh {CONFIG["pi_user"]}@{CONFIG["pi_host"]} "cd {CONFIG["pi_project_path"]} && git pull"'
    success, _ = run_command(cmd)
    if not success:
        add_log("Pull on Pi failed", "error")
        return jsonify({"success": False, "error": "Pull on Pi failed"})
    
    # 4. Restart on Pi
    cmd = f'ssh {CONFIG["pi_user"]}@{CONFIG["pi_host"]} "screen -S powerball -X quit 2>/dev/null; cd {CONFIG["pi_project_path"]} && screen -dmS powerball bash -c \'source venv/bin/activate && python main.py\'"'
    success, _ = run_command(cmd)
    
    add_log("=== DEPLOY COMPLETE ===", "success")
    return jsonify({"success": True})

@app.route('/api/get_logs', methods=['POST'])
def get_logs():
    return jsonify({"logs": logs})

@app.route('/api/clear_logs', methods=['POST'])
def clear_logs():
    global logs
    logs = []
    add_log("Logs cleared")
    return jsonify({"success": True})


if __name__ == '__main__':
    print("=" * 50)
    print("POWERBALL DEV PANEL")
    print("=" * 50)
    print(f"\nOpen in browser: http://localhost:{CONFIG['dev_panel_port']}")
    print(f"\nPi Target:")
    print(f"  Host: {CONFIG['pi_host']}")
    print(f"  User: {CONFIG['pi_user']}")
    print(f"  Path: {CONFIG['pi_project_path']}")
    print("\nWorkflow: Edit code -> Click 'Deploy to Pi' -> Done!")
    print("\nPress Ctrl+C to exit")
    print("=" * 50)

    app.run(host='127.0.0.1', port=CONFIG['dev_panel_port'], debug=False)
