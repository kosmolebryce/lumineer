import subprocess
import sys
import os

if __name__ == "__main__":
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the command to run the Lumineer package
    lumineer_command = [sys.executable, "-m", "lumineer.flashcards"]
    
    # Use subprocess to run Lumineer without showing a console
    if sys.platform.startswith('win'):
        # For Windows, use CREATE_NO_WINDOW flag
        subprocess.Popen(lumineer_command,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        # For non-Windows platforms, redirect output to devnull
        with open(os.devnull, 'w') as devnull:
            subprocess.Popen(lumineer_command,
                             stdout=devnull,
                             stderr=devnull)
