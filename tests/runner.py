#!/usr/bin/env python3

import os
import sys
import signal
import subprocess

def start_program(program_name):
    # Ensure the program exists in the same directory
    program_path = os.path.join(os.getcwd(), program_name)
    if not os.path.isfile(program_path) or not os.access(program_path, os.X_OK):
        print(f"Error: '{program_name}' not found or not executable in the current directory.")
        sys.exit(1)

    # Execute and disown the program
    try:
        subprocess.Popen([program_path], stdin=None, stdout=None, stderr=None, close_fds=True)
        print(f"Program '{program_name}' started successfully.")
    except Exception as e:
        print(f"Error starting program: {e}")
        sys.exit(1)

def stop_program(program_name):
    # Find and terminate the program's process
    try:
        # Use pgrep to find the program's PID
        result = subprocess.run(
            ['pgrep', '-f', program_name],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        # Extract PIDs from the output
        pids = result.stdout.strip().splitlines()
        if not pids:
            print(f"No running instances of '{program_name}' found.")
            sys.exit(1)

        # Send SIGTERM to each PID
        for pid in pids:
            os.kill(int(pid), signal.SIGTERM)
            print(f"Stopped process {pid} for program '{program_name}'.")

    except subprocess.CalledProcessError:
        print(f"No running instances of '{program_name}' found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error stopping program: {e}")
        sys.exit(1)


def main(program_name, action):
    if action == 'start':
        start_program(program_name)
    elif action == 'stop':
        stop_program(program_name)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ['start', 'stop']:
        print("Usage: ./runner.py <program_name> <start|stop>")
        sys.exit(1)

    program_name = sys.argv[1]
    action = sys.argv[2]

    main(program_name, action)
