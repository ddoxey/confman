"""
Tests for the Control process controller class.
"""
import os
import unittest
from time import sleep
from control import Control

# Path to the directory containing the sample executables
BIN_DIR = "tests"


class TestControl(unittest.TestCase):
    """
    Demonstrate and test features of the Control process controller class.
    """
    def setUp(self):
        """
        Set up the test environment.
        """
        self.sample_processes = [
            {'cwd': BIN_DIR,
             'ex_name': 'sample_one',
             'children': ['sample_one.1', 'sample_one.2', 'sample_one.3']},
            {'cwd': BIN_DIR,
             'ex_name': 'sample_two'},
        ]
        # Ensure all processes exist
        for process in self.sample_processes:
            full_path = os.path.realpath(os.path.join(process['cwd'],
                                         process['ex_name']))
            self.assertTrue(
                os.path.exists(full_path) and os.access(full_path, os.X_OK),
                f"Executable {process['ex_name']} missing or not executable."
            )

    def test_properties_name(self):
        """
        Test that the various properties are initialized correctly.
        """
        proc = {'name': 'ls'}
        expect = {
            'name': proc['name'],
            'ex_name': proc['name'],
            'ps_name': proc['name'],
            'cmd': [],
            'cwd': None,
            'children': []
        }
        control = Control(proc)
        for attr, val in expect.items():
            self.assertEqual(control.get(attr), val,
                             f'Failed to set correct {attr} value')

    def test_properties_cmd(self):
        """
        Test that the various properties are initialized correctly.
        """
        proc = {'cmd': ['ls', '-l', '/tmp']}
        expect = {
            'name': proc['cmd'][0],
            'ex_name': proc['cmd'][0],
            'ps_name': proc['cmd'][0],
            'cmd': proc['cmd'][1:],
            'cwd': None,
            'children': []
        }
        control = Control(proc)
        for attr, val in expect.items():
            self.assertEqual(control.get(attr), val,
                             f'Failed to set correct {attr} value')

    def test_properties_cwd_a(self):
        """
        Test that the various properties are initialized correctly.
        """
        proc = {'ex_name': 'ls', 'cwd': 'tests'}
        expect = {
            'name': proc['ex_name'],
            'ex_name': proc['ex_name'],
            'ps_name': proc['ex_name'],
            'cmd': [],
            'cwd': 'tests',
            'children': []
        }
        control = Control(proc)
        for attr, val in expect.items():
            self.assertEqual(control.get(attr), val,
                             f'Failed to set correct {attr} value')

    def test_properties_cwd_b(self):
        """
        Test that the various properties are initialized correctly.
        """
        proc = {'ex_name': 'sample_one',
                'cwd': 'tests',
                'children': ['sample_one.1', 'sample_one.2', 'sample_one.3']}
        expect = {
            'name': proc['ex_name'],
            'ex_name': f"./{proc['ex_name']}",
            'ps_name': proc['ex_name'],
            'cmd': [],
            'cwd': 'tests',
            'children': proc['children']
        }
        control = Control(proc)
        for attr, val in expect.items():
            self.assertEqual(control.get(attr), val,
                             f'Failed to set correct {attr} value')

    def test_start_stop(self):
        """
        Test that processes start and stop correctly.
        """
        for process in self.sample_processes:
            control = Control(process)
            status = control.start()
            self.assertNotEqual(status, Control.STOPPED,
                                f"{control.get_name()} failed to start.")
            sleep(1)  # Allow time to spawn children
            self.assertEqual(control.get_status(), Control.RUNNING,
                             f"{control.get_name()} not running.")
            control.stop()
            self.assertEqual(control.get_status(), Control.STOPPED,
                             f"{control.get_name()} running.")

    def test_start_stop_multiple(self):
        """
        Test that processes start/stop correctly across multiple instances.
        """
        for process in self.sample_processes:
            control_a = Control(process)
            status = control_a.start()
            self.assertNotEqual(status, Control.STOPPED,
                                f"a) {control_a.get_name()} failed to start.")
            sleep(1)  # Allow time to spawn children
            self.assertEqual(control_a.get_status(), Control.RUNNING,
                             f"a) {control_a.get_name()} not running.")
            control_b = Control(process)
            self.assertEqual(control_b.get_status(), Control.RUNNING,
                             f"b) {control_b.get_name()} not running.")
            control_b.stop()
            self.assertEqual(control_b.get_status(), Control.STOPPED,
                             f"b) {control_b.get_name()} running.")
            self.assertEqual(control_a.get_status(), Control.STOPPED,
                             f"a) {control_a.get_name()} running.")

    def test_restart(self):
        """
        Test restarting a process.
        """
        for process in self.sample_processes:
            control = Control(process)
            control.start()
            sleep(1)  # Allow process to initialize
            control.stop()
            sleep(1)  # Allow process to terminate
            status = control.start()
            self.assertNotEqual(status, Control.STOPPED,
                                f"{control.get_name()} failed to restart.")
            sleep(1)
            self.assertEqual(control.get_status(), Control.RUNNING,
                             f"{control.get_name()} not running.")

    def tearDown(self):
        """
        Clean up by stopping any running processes.
        """
        for process in self.sample_processes:
            control = Control(process)
            if control.get_status() == Control.RUNNING:
                control.stop()


if __name__ == "__main__":
    unittest.main()
