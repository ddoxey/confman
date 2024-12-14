from pprint import pprint
import os
import shutil
import subprocess


class Control:
    """
    Abstract layer for managing processes using subprocess.
    """

    RUNNING = 1
    JEOPARDY = 0
    STOPPED = -1

    def __init__(self, process):
        """
        Initialize the control for a process.
        :param process: dict of:
            name : name of the process 
            cmd : tokens of shell command to execute
            ex_name : executable filename (defaults to name)
            ps_name : process table name (default to name)
            children : list of process table names for child processes
        """
        self.name = process.get('name', None)
        self.cmd = process.get('cmd', None)
        if self.cmd is not None and len(self.cmd) > 0:
            self.ex_name = self.cmd[0]
            self.cmd = self.cmd[1:]
        else:
            self.ex_name = process.get('ex_name', self.name)
            self.cmd = []
        self.ps_name = process.get('ps_name', self.name)
        self.children = process.get('children', [])
        self.cwd = process.get('cwd', None)
        if self.ex_name is None:
            raise ValueError(f'{__class__} requires process "name" property')
        if self.cwd is not None:
            full_path = os.path.realpath(os.path.join(self.cwd, self.ex_name))
            if os.path.exists(full_path):
                self.cwd = os.path.dirname(full_path)
                self.ex_name = os.path.join('.', os.path.basename(full_path))
        else:
            full_path = shutil.which(self.ex_name)
            if full_path is None:
                full_path = os.path.realpath(os.path.join(os.getcwd(), self.ex_name))
                if os.path.exists(full_path):
                    self.cwd = os.path.dirname(full_path)
                    self.ex_name = os.path.join('.', os.path.basename(full_path))
        self.process = None

    def get_name(self):
        """
        The configured process name.
        """
        return self.name

    def start(self):
        """
        Start the process if it is not already running.
        """
        if self.get_status() == self.STOPPED:
            cmd = [self.ex_name]
            if len(self.cmd) > 0:
                cmd.extend(self.cmd)
            pprint({'cmd': cmd, 'cwd': self.cwd})
            self.process = subprocess.Popen([self.ex_name, *self.cmd],
                                            cwd=self.cwd,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
        return self.get_status()

    def stop(self):
        """
        Stop the process if it is running.
        """
        pids = []
        for child in self.children:
            child_pid = self.get_pidof(child)
            if child_pid is not None:
                pids.extend(child_pid)
        pid = self.get_pidof(self.ps_name)
        if pid is not None:
            pids.extend(pid)
        if len(pids) > 0:
            self.kill(pids)
        return self.is_running()

    def get_status(self):
        """
        Determine the running status of the process.
        :return: RUNNING, JEOPARDY, STOPPED
        """
        pid = self.get_pidof(self.ps_name)
        child_count = 0
        for child in self.children:
            child_pid = self.get_pidof(child)
            if child_pid is not None:
                child_count += 1
        if pid is None:
            if child_count == 0:
                return self.STOPPED
            return self.JEOPARDY
        if len(self.children) != child_count:
            return self.JEOPARDY
        return self.RUNNING

    def is_running(self):
        """
        Check if the process is running.
        :return: True if not STOPPED, False otherwise.
        """
        return self.get_status() != self.STOPPED

    def get_pidof(self, ps_name):
        """
        Get a list of one or more pids for the given process table name
        :return: list of one or more pids None.
        """
        pids = None
        try:
            result = subprocess.check_output(['pidof', ps_name]).strip()
            pids = result.strip().split()
            if len(pids) == 0:
                pids = None
        except subprocess.CalledProcessError:
            pass
        return pids

    def kill(self, pids):
        """
        Kill a list of process IDs
        :return: True on success
        """
        try:
            if isinstance(pids, str):
                pids = [pids]
            subprocess.check_output(['kill', *pids])
        except subprocess.CalledProcessError:
            return False
        return True
