#!/usr/bin/env python3
"""
ReimburseAI - Autonomous Expense & Reimbursement Assistant
Dynamic Cross-Platform Startup Runner

Usage:
    python run.py                   # Run on default port (8000 or next available)
    python run.py --port 8080       # Run on custom port
    python run.py --host 0.0.0.0    # Bind to specific host
    python run.py --install         # Force install dependencies
    python run.py --build           # Build frontend before starting
"""

import os
import sys
import socket
import shutil
import argparse
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def check_and_install_dependencies():
    """Verifies that all required packages are installed, prompting or auto-installing if missing."""
    required_packages = ["fastapi", "uvicorn", "pydantic", "pypdf", "PIL", "reportlab"]
    missing = []
    
    for pkg in required_packages:
        try:
            if pkg == "PIL":
                __import__("PIL")
            else:
                __import__(pkg)
        except ImportError:
            missing.append(pkg)
            
    if missing:
        print(f"\n[!] Missing required Python packages: {', '.join(missing)}")
        req_file = os.path.join(BASE_DIR, "requirements.txt")
        if os.path.exists(req_file):
            print("[*] Installing dependencies from requirements.txt...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
                print("[+] Dependencies installed successfully!\n")
            except Exception as e:
                print(f"[-] Failed to auto-install dependencies: {e}")
                print(f"[!] Please manually run: pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("[!] requirements.txt not found. Please install dependencies manually.")
            sys.exit(1)

def ensure_env_file():
    """Creates a local .env file from .env.example if not present."""
    env_file = os.path.join(BASE_DIR, ".env")
    example_file = os.path.join(BASE_DIR, ".env.example")
    if not os.path.exists(env_file) and os.path.exists(example_file):
        try:
            shutil.copy(example_file, env_file)
            print("[+] Initialized local .env from .env.example")
        except Exception:
            pass

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a network port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def find_available_port(start_port: int, host: str = "127.0.0.1", max_attempts: int = 20) -> int:
    """Finds the first free port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(p, host):
            return p
    return start_port

def build_frontend_if_needed(force: bool = False):
    """Builds the React frontend if dist is missing or if force=True."""
    dist_dir = os.path.join(BASE_DIR, "frontend", "dist")
    frontend_dir = os.path.join(BASE_DIR, "frontend")
    
    needs_build = force or not os.path.exists(dist_dir) or not os.path.exists(os.path.join(dist_dir, "index.html"))
    if needs_build and os.path.exists(frontend_dir):
        npm_cmd = shutil.which("npm") or ("npm.cmd" if sys.platform == "win32" else None)
        if npm_cmd:
            print("[*] Building production frontend with Vite...")
            try:
                # Run npm install if node_modules missing
                if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
                    print("[*] Installing frontend node dependencies...")
                    subprocess.check_call([npm_cmd, "install"], cwd=frontend_dir)
                subprocess.check_call([npm_cmd, "run", "build"], cwd=frontend_dir)
                print("[+] Frontend built successfully!\n")
            except Exception as e:
                print(f"[!] Notice: Frontend build failed ({e}). Backend will run with fallback UI.")
        else:
            if not os.path.exists(dist_dir):
                print("[!] Note: Node.js/npm is not detected. Pre-built frontend will be used if present.")

def ensure_sample_data():
    """Generates the 11 realistic sample receipt files on first run."""
    sample_dir = os.path.join(BASE_DIR, "backend", "sample_receipts")
    os.makedirs(sample_dir, exist_ok=True)
    if len(os.listdir(sample_dir)) < 11:
        try:
            from backend.demo_generator import generate_sample_batch_files
            print("[*] Generating 11 realistic sample receipt files (images & PDFs)...")
            generate_sample_batch_files(sample_dir)
            print("[+] Sample receipt batch generated successfully!")
        except Exception as e:
            print(f"[!] Warning: Could not generate sample batch: {e}")

def main():
    parser = argparse.ArgumentParser(description="ReimburseAI - Autonomous Expense & Reimbursement Assistant")
    parser.add_argument("--host", default=None, help="Host interface to bind (default: 0.0.0.0 or from HOST env)")
    parser.add_argument("--port", type=int, default=None, help="Port to listen on (default: 8000 or next free port)")
    parser.add_argument("--reload", action="store_true", default=False, help="Enable auto-reload on code change")
    parser.add_argument("--install", action="store_true", help="Install requirements before running")
    parser.add_argument("--build", action="store_true", help="Force rebuild frontend before running")
    args = parser.parse_args()

    print("=" * 68)
    print("  ReimburseAI - Autonomous Expense & Reimbursement Assistant")
    print("=" * 68)

    # 1. Ensure dependencies are satisfied
    if args.install:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        check_and_install_dependencies()

    # 2. Setup local environment
    ensure_env_file()

    # 3. Build frontend if needed
    build_frontend_if_needed(force=args.build)

    # 4. Ensure demo sample receipts are available
    ensure_sample_data()

    # 5. Resolve host and port dynamically
    env_host = os.environ.get("HOST", "0.0.0.0")
    env_port = int(os.environ.get("PORT", "8000"))
    
    target_host = args.host or env_host
    desired_port = args.port or env_port

    # If desired port is occupied, automatically locate next free port
    actual_port = desired_port
    if is_port_in_use(desired_port, "127.0.0.1"):
        free_port = find_available_port(desired_port, "127.0.0.1")
        if free_port != desired_port:
            print(f"\n[!] Port {desired_port} is currently in use.")
            print(f"[*] Dynamically switching to available port: {free_port}")
            actual_port = free_port

    display_host = "localhost" if target_host in ["0.0.0.0", "127.0.0.1"] else target_host

    print("\n" + "-" * 68)
    print(f"  * Web Application:   http://{display_host}:{actual_port}")
    print(f"  * Admin Portal:      http://{display_host}:{actual_port}/admin")
    print(f"  * Interactive Docs:  http://{display_host}:{actual_port}/docs")
    print(f"  * Technical PDF:     http://{display_host}:{actual_port}/api/tdd-pdf")
    print("-" * 68)
    print("\nPress Ctrl+C to stop the server.\n")

    try:
        import uvicorn
        uvicorn.run("backend.main:app", host=target_host, port=actual_port, reload=args.reload)
    except KeyboardInterrupt:
        print("\n[*] ReimburseAI server stopped cleanly. Goodbye!")

if __name__ == "__main__":
    main()
