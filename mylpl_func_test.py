# -*- coding: utf-8 -*-
import unittest
import subprocess
import os
import inspect
import filecmp

SCRIPT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
MYLPL_SCRIPT = os.path.join(SCRIPT_PATH, 'mylpl.py')
TEST_DATA_DIR = os.path.join(SCRIPT_PATH, 'test_data')

import mylpl


class FunctionalTestsMyLedgerPal(unittest.TestCase):

    # --------------------------- Utils --------------------------------

    def _spawn_process(self, args):
        # args.append('--debug')
        p = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p

    def _print_func_name(self, functest=False):
        print("\n-----------------------------------------------------------")
        if functest:
            print("FuncTest: {0}".format(inspect.stack()[1][3]))
        else:
            print("UnitTest: {0}".format(inspect.stack()[1][3]))
        print("-----------------------------------------------------------")

    # ------------------------ MyLedgerPal -----------------------------

    def test_001_clean_previous_state(self):
        for root, dirs, files in os.walk(TEST_DATA_DIR):
            for currentFile in files:
                fn = currentFile.lower()
                if '.bak' in fn or fn == "rbc.ledger":
                    os.remove(os.path.join(root, currentFile))

    def test_002_display_banklist(self):
        self._print_func_name(functest=True)
        p = self._spawn_process(["python", MYLPL_SCRIPT, "-l"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue("Available banks" in out)

    def test_003_display_help(self):
        self._print_func_name(functest=True)
        p = self._spawn_process(["python", MYLPL_SCRIPT, "-h"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue("mypl" in out)

    def test_004_unknown_bank(self):
        self._print_func_name(functest=True)
        b = "ubank"
        p = self._spawn_process(["python", MYLPL_SCRIPT, b, "dummy_input"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue(mylpl.ERR_BANK_UNKNOWN.format(b) in out)

    def test_005_unknown_input(self):
        self._print_func_name(functest=True)
        p = self._spawn_process(
            ["python", MYLPL_SCRIPT, "RBC", "invalid_input"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue(mylpl.ERR_INPUT_UNKNOWN in out)

    def test_006_bank_valid_but_no_input(self):
        self._print_func_name(functest=True)
        p = self._spawn_process(["python", MYLPL_SCRIPT, "RBC"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue("Usage:" in err)

    def test_007_run(self):
        self._print_func_name(functest=True)
        input = os.path.join(TEST_DATA_DIR, "RBC.csv")
        output = os.path.join(TEST_DATA_DIR, "RBC.ledger")
        app = mylpl.MyLedgerPal('RBC', input, output)
        app.run()

    def test_008_run_insert_post(self):
        self._print_func_name(functest=True)
        input = os.path.join(TEST_DATA_DIR, "RBC2.csv")
        output = os.path.join(TEST_DATA_DIR, "RBC.ledger")
        app = mylpl.MyLedgerPal('RBC', input, output)
        app.run()

    def test_009_exepcted_result(self):
        result = os.path.join(TEST_DATA_DIR, "RBC.ledger")
        expected = os.path.join(TEST_DATA_DIR, "RBC.ledger.expected")
        self.assertTrue(filecmp.cmp(result, expected))

if __name__ == '__main__':
    unittest.main()
