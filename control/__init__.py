from pprint import pprint
import sys
import os
import time
import shutil
import subprocess


class Control:
    """
    Abstraction layer for managing processes using subprocess.
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
        self.ps_name = process.get('ps_name', process.get('name', self.ex_name))
        if self.name is None:
            self.name = self.ex_name
        self.children = process.get('children', [])
        self.cwd = process.get('cwd', None)

        if self.ex_name is None:
            raise ValueError(f'{__class__} requires process "name" property')

        if self.cwd is not None:
            if not os.path.exists(self.cwd):
                print(f'No such directory: {self.cwd}',
                      file=sys.stderr, flush=True)
                self.cwd = None
            elif not os.path.isdir(self.cwd):
                print(f'Not a directory: {self.cwd}',
                      file=sys.stderr, flush=True)
                self.cwd = None

        full_ex_path = None
        if not os.path.exists(self.ex_name):
            full_ex_path = shutil.which(self.ex_name)
            if full_ex_path is None:
                if self.cwd is not None:
                    full_ex_path = os.path.realpath(os.path.join(self.cwd, self.ex_name))
                    if os.path.exists(full_ex_path):
                        self.ex_name = os.path.join('.', os.path.basename(full_ex_path))
        if full_ex_path is None or not os.path.exists(full_ex_path):
            print(f'Unable to locate executable: {self.ex_name}',
                  file=sys.stderr, flush=True)
        self.process = None

    def get_name(self):
        """
        Get the process name.
        """
        return self.name

    def get(self, prop):
        """
        Get properties of the initialized control instance
        :return: None if undefined or non-existant
        """
        return getattr(self, prop, None)

    def start(self):
        """
        Start the process if it is not already running.
        Ensure the process is disowned after spawning.
        """
        if self.get_status() == self.STOPPED:
            cmd = [self.ex_name] + self.cmd
            try:
                self.process = subprocess.Popen(
                    cmd,
                    cwd=self.cwd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True  # Disown the process
                )
                # Squelch ResourceWarning warning on destruction
                self.process.returncode = 0
            except FileNotFoundError:
                print(f"Error: Executable '{self.ex_name}' not found.",
                      file=sys.stderr, flush=True)
                return self.STOPPED
        return self.get_status()

    def stop(self):
        """
        Stop the process and all of its children. For this procedure
        all of the children named in process configuration, in addition
        to processes appearing in the process table as children.
        """
        ppids = self.get_pidof(self.ps_name)
        named_cpids = self.get_pidof(self.children)
        cpids = self.get_child_pids(list(set(ppids + named_cpids)))
        pids = sorted(list(set(ppids + named_cpids + cpids)), key=int)
        if len(pids) == 0:
            return self.STOPPED
        if len(ppids) > 0:
            self.kill(ppids)
            time.sleep(0.5)
        if len(named_cpids) > 0:
            self.kill(named_cpids)
            time.sleep(0.5)
        if len(cpids) > 0:
            self.kill(cpids)
            time.sleep(0.5)
        for signal in ['-SIGTERM', '-SIGTERM', '-SIGKILL']:
            if not self.any_alive(pids):
                return self.STOPPED
            self.kill(pids, signal)
            time.sleep(0.5)
        return self.is_running()

    def get_status(self):
        """
        Determine the running status of the process.
        RUNNING : Defined by the primary process and all named child
        processes appearing with at least one PID in the process table.
        JEOPARDY : Defined by some of the expected processes appearing
        in the process table.
        STOPPED : Defined by none of the expected processes appearing
        in the process table.
        :return: RUNNING, JEOPARDY, STOPPED
        """
        pids = self.get_pidof(self.ps_name)
        named_cpids = self.get_pidof(self.children)
        if len(pids) == 0:
            if len(named_cpids) == 0:
                return self.STOPPED
            return self.JEOPARDY
        if len(named_cpids) > 0:
            if len(self.children) != len(named_cpids):
                return self.JEOPARDY
        return self.RUNNING

    def is_running(self):
        """
        Check if the process is running.
        :return: True if not STOPPED, False otherwise.
        """
        return self.get_status() != self.STOPPED

    def get_pidof(self, ps_names):
        """
        Get a list of one or more pids for the given process table name
        :return: list of one or more pids None.
        """
        if isinstance(ps_names, str):
            ps_names = [ps_names]
        pids = []
        try:
            cmd = ['pidof', *ps_names]
            result = subprocess.check_output(cmd).strip()
            pids = [pid.decode('utf-8') for pid in result.strip().split()]
        except subprocess.CalledProcessError:
            pass
        return pids

    def get_pids(self):
        """
        Get process IDs for the named children and parent processe(s).
        return: list of zero or more child PIDs and PID(s) as last entry
        """
        pids = []
        child_pids = self.get_pidof(self.children)
        if len(child_pids) > 0:
            pids.extend(child_pids)
        pid = self.get_pidof(self.ps_name)
        if len(pid) > 0:
            pids.extend(pid)
        return pids

    def get_child_pids(self, pids):
        """
        Scan the process table to find process IDs for children of the
        given list of parent PIDs. (Unlike pgrep, this process doesn't rely
        on child processes having a like process name to the parent.)
        :return: list of child PIDs
        """
        child_pids = []
        if len(pids) > 0:
            return child_pids
        ps_out = None
        try:
            cmd = ['ps', 'ax', '-o', 'pid,ppid']
            ps_out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            pass
        if ps_out is not None:
            for line in ps_out.decode('utf-8').split('\n'):
                pid, ppid = line.split()
                if ppid in pids:
                    child_pids.append(pid)
        return child_pids

    def get_defunct_pids(self, pids):
        """
        :return: list of defunct PIDs
        """
        defunct_pids = []
        if len(pids) > 0:
            return defunct_pids
        ps_out = None
        try:
            cmd = ['ps', 'ax', '-o', 'pid,command']
            ps_out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            pass
        if ps_out is not None:
            for line in ps_out.decode('utf-8').split('\n'):
                pid, command = line.split()
                if pid in pids and '<defunc>' in command:
                    defunct_pids.append(pid)
        return defunct_pids

    def any_alive(self, pids):
        """
        This determines if any of the given process IDs are still running.
        :return: True if any are alive
        """
        if len(pids) == 0:
            return False
        return self.kill(pids, '-0')

    def kill(self, pids, signal='-SIGTERM'):
        """
        Kill a list of process IDs
        :return: True on success
        """
        status = 1
        if isinstance(pids, str):
            pids = [pids]
        try:
            cmd = ['kill', signal, *pids]
            result = subprocess.run(
                cmd,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                check=True  # Raise CalledProcessError for non-zero exit codes
            )
            status = result.returncode
        except subprocess.CalledProcessError as e:
            status = e.returncode
        return status == 0
