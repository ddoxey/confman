import os
import shutil
import subprocess

class Control:
    """
    Abstract layer for managing processes using subprocess.
    """

    def __init__(self, bin_name, cwd=None):
        """
        Initialize the control for a process.
        :param bin_name: Path to the executable binary.
        :param cwd: Working directory for the process.
        """
        if cwd is None:
            full_path = shutil.which(bin_name)
            if full_path is not None:
                cwd = os.path.dirname(full_path)
            else:
                cwd = os.getcwd()
        self.bin_name = bin_name
        self.cwd = cwd
        self.process = None

    def start(self):
        """
        Start the process if it is not already running.
        """
        if not self.is_running():
            self.process = subprocess.Popen(
                [self.bin_name], cwd=self.cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            return f"Process {self.bin_name} started."
        return f"Process {self.bin_name} is already running."

    def stop(self):
        """
        Stop the process if it is running.
        """
        if self.is_running():
            self.process.terminate()
            self.process.wait()
            self.process = None
            return f"Process {self.bin_name} stopped."
        return f"Process {self.bin_name} is not running."

    def is_running(self):
        """
        Check if the process is running.
        :return: True if running, False otherwise.
        """
        return self.process is not None and self.process.poll() is None
