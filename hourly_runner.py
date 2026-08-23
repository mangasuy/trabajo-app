
"""
Hourly runner for server/cron use.

A real server can schedule:
    python server/hourly_runner.py
every 60 minutes with cron/systemd/GitHub Actions/hosting scheduler.
"""
from pathlib import Path
import subprocess, sys

ROOT=Path(__file__).resolve().parent.parent

def run(script):
    p=ROOT/script
    if p.exists():
        print(">", script)
        subprocess.run([sys.executable,str(p)],cwd=ROOT,check=False)

if __name__=="__main__":
    run("buscojobs_connector.py")
    run("buscojobs_full_parser.py")
    run("scoring_engine_v2.py")
    run("server/pipeline.py")
