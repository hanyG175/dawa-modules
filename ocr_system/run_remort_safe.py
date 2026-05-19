import argparse
import subprocess
import argparse
import subprocess
import sys
import threading
import os
import time

parser = argparse.ArgumentParser(description='Safely run remort_neo_connection.py with timeout')
parser.add_argument('--timeout', type=int, default=20, help='Seconds before force-kill')
args = parser.parse_args()

SCRIPT = os.path.join(os.path.dirname(__file__), 'remort_neo_connection.py')
if not os.path.exists(SCRIPT):
    print('Error: remort_neo_connection.py not found in workspace')
    sys.exit(2)

print(f"Running {SCRIPT} with timeout {args.timeout}s")

def _reader(stream, prefix):
    try:
        for line in iter(stream.readline, ''):
            if not line:
                break
            print(f"{prefix}{line.rstrip()}")
    except Exception:
        pass

proc = subprocess.Popen([sys.executable, SCRIPT], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

stdout_thread = threading.Thread(target=_reader, args=(proc.stdout, 'OUT: '), daemon=True)
stderr_thread = threading.Thread(target=_reader, args=(proc.stderr, 'ERR: '), daemon=True)

stdout_thread.start()
stderr_thread.start()

try:
    start = time.time()
    proc.wait(timeout=args.timeout)
    elapsed = time.time() - start
    print(f"Process exited (code={proc.returncode}) after {elapsed:.1f}s")
except subprocess.TimeoutExpired:
    print(f"⚠️ TimeoutExpired after {args.timeout}s — killing process")
    try:
        proc.kill()
    except Exception as e:
        print(f"Failed to kill process: {e}")
    finally:
        try:
            proc.wait(timeout=5)
        except Exception:
            pass

    print('Process killed due to timeout')

# Give reader threads a moment to flush
time.sleep(0.5)
print('Done.')
