import sys
import subprocess
from pathlib import Path

def main():
    root = Path(__file__).parent.resolve()
    webapp_path = root.parent / "src" / "web" / "app.py"
    
    # ensure it's loaded properly
    if not webapp_path.exists():
        print(f"Error: Could not find web app script at {webapp_path}")
        return 1

    try:
        # We start the Flask server
        print("Launching Real Web App using Flask/Tailwind...")
        subprocess.check_call([sys.executable, str(webapp_path)])
    except KeyboardInterrupt:
        print("\nShutdown Web App Server.")
    except Exception as e:
        print(f"Error executing web app: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
