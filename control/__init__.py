from pprint import pformat
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
        self.pidof_path = shutil.which('pidof')
        self.kill_path = shutil.which('kill')
        self.ps_path = shutil.which('ps')
        self.cwd = process.get('cwd', None)
        self.cmd = process.get('cmd', None)
        self.start_cmd = process.get('start_cmd', self.cmd)
        self.stop_cmd = process.get('stop_cmd', None)
        self.name = process.get('name', None)
        self.ex_name = process.get('ex_name', self.name)
        self.ps_name = process.get('ps_name', None)
        self.children = process.get('children', [])

        if isinstance(self.children, str):
            self.children = self.children.strip().split()

        if self.cwd is not None:
            if not os.path.exists(self.cwd):
                print(f'No such directory: {self.cwd}',
                      file=sys.stderr, flush=True)
                self.cwd = None
            elif not os.path.isdir(self.cwd):
                print(f'Not a directory: {self.cwd}',
                      file=sys.stderr, flush=True)
                self.cwd = None

        if self.start_cmd is None or len(self.start_cmd) == 0:
            self.start_cmd = self._make_start_cmd()
        else:
            self.start_cmd = self._validate_cmd(self.start_cmd)
            self.ex_name = self.start_cmd[0]

        if self.stop_cmd is not None:
            self.stop_cmd = self._validate_cmd(self.stop_cmd)

        if self.start_cmd is None:
            raise ValueError(f'{__class__.__name__} unable to determine what to execute')
        if self.ps_name is None:
            self.ps_name = os.path.basename(self.ex_name)
        if self.name is None:
            self.name = self.ps_name

    def _validate_cmd(self, cmd):
        if cmd is None or len(cmd) == 0:
            return None
        ex_name = cmd[0]
        ex_path = shutil.which(ex_name)
        if ex_path is not None:
            ex_path = ex_name
        else:
            cwd = os.getcwd() if self.cwd is None else self.cwd
            ex_path = os.path.realpath(os.path.join(cwd, ex_name))
            if os.path.exists(ex_path):
                ex_path = os.path.join('.', os.path.basename(ex_path))
        if ex_path is None:
            print(f'Unable to locate executable: {ex_name}',
                    file=sys.stderr, flush=True)
            return None
        cmd[0] = ex_path
        return cmd

    def _make_start_cmd(self):
        """
        This does the work of making a start command list suitable for passing
        directly to subprocess.Popen(..)
        """
        if self.ex_name is None:
            return None
        ex_path = None
        if not os.path.exists(self.ex_name):
            ex_path = shutil.which(self.ex_name)
            if ex_path is not None:
                ex_path = self.ex_name
            else:
                cwd = os.getcwd() if self.cwd is None else self.cwd
                ex_path = os.path.realpath(os.path.join(cwd, self.ex_name))
                if os.path.exists(ex_path):
                    self.ex_name = os.path.join('.', os.path.basename(ex_path))
                    ex_path = self.ex_name
        if ex_path is None:
            print(f'Unable to locate executable: {self.ex_name}',
                  file=sys.stderr, flush=True)
            return None
        return [ex_path]

    def _run(self, cmd):
        """
        Run the given command list.
        :return: True on success
        """
        pid = os.fork()
        if pid == 0:
            # sacraficial child intermediate process
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd=self.cwd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True  # Disown the process
                )
                # Squelch ResourceWarning warning on destruction
                process.returncode = 0
            except FileNotFoundError:
                print(f"Error: Executable '{cmd[0]}' not found (cwd={self.cwd}).",
                        file=sys.stderr, flush=True)
                os._exit(1)
            os._exit(0)
        return True

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
            self._run(self.start_cmd)
        for check in range(3):
            if self.get_status() == self.RUNNING:
                return self.RUNNING
            time.sleep(0.5)
        return self.get_status()

    def stop(self):
        """
        Stop the process and all of its children. For this procedure
        all of the children named in process configuration, in addition
        to processes appearing in the process table as children.
        """
        if self.stop_cmd is not None:
            self._run(self.stop_cmd)
            for check in range(3):
                if self.get_status() == self.STOPPED:
                    return self.STOPPED
                time.sleep(0.5)
        else:
            ppids = self.get_pidof(self.ps_name)
            named_cpids = self.get_pidof(self.children)
            cpids = self.get_child_pids(list(set(ppids + named_cpids)))
            child_pids = sorted(list(set(named_cpids + cpids)), key=int)
            pids = sorted(list(set(ppids + child_pids)), key=int)
            if len(pids) == 0:
                # nothing is running already
                return self.STOPPED
            if len(child_pids) > 0:
                self.kill(child_pids)
            if len(ppids) > 0:
                self.kill(ppids)
            for signal in ['-SIGTERM', '-SIGKILL', '-SIGKILL']:
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
            ps_names = ps_names.split()
        pids = []
        try:
            cmd = [self.pidof_path, *ps_names]
            result = subprocess.check_output(cmd).strip()
            pids = result.decode('utf-8').strip().split()
        except subprocess.CalledProcessError as pce:
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
            cmd = [self.ps_path, 'ax', '-o', 'pid,ppid']
            ps_out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            pass
        if ps_out is not None:
            for line in ps_out.decode('utf-8').split('\n'):
                if len(line.strip()) > 0:
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
            cmd = [self.ps_path, 'ax', '-o', 'pid,command']
            ps_out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            pass
        if ps_out is not None:
            for line in ps_out.decode('utf-8').split('\n'):
                if len(line.strip()) > 0:
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
            pids = pids.split()
        try:
            cmd = [self.kill_path, signal, *pids]
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
