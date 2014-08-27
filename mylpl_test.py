import unittest
import subprocess
import os
import shutil
import inspect
from mock import patch

SCRIPT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
MYPL_SCRIPT = os.path.join(SCRIPT_PATH, 'mylpl.py')
TEST_DATA_DIR = os.path.join(SCRIPT_PATH, 'test_data')

import mylpl


def static_var(varname, value):
    ''' Decorator to declare a function static variable. '''
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate


class TestMyLedgerPal(unittest.TestCase):

    def _spawn_process(self, args):
        args.append('--debug')
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

    def _get_myledgerpal_obj(self):
        input = os.path.join(TEST_DATA_DIR, "RBC.csv")
        output = os.path.join(TEST_DATA_DIR, "RBC.ledger")
        return mylpl.MyLedgerPal('RBC', input, output)

    def _get_bank_definition(self):
        return {mylpl.MyLedgerPal.BANK_ENCODING: "utf-8",
                mylpl.MyLedgerPal.BANK_QUOTE_CHAR: "'",
                mylpl.MyLedgerPal.BANK_DELIMITER: ":",
                mylpl.MyLedgerPal.BANK_COLNAME_ACC_NUM: 1,
                mylpl.MyLedgerPal.BANK_COLNAME_DATE: 2,
                mylpl.MyLedgerPal.BANK_COLNAME_CHECK_NUM: 3,
                mylpl.MyLedgerPal.BANK_COLNAME_DESC: [4, 5],
                mylpl.MyLedgerPal.BANK_COLNAME_AMOUNT: 6}

    # Unit Tests
    # ------------------------------------------------------------------------

    @patch.object(shutil, "copyfile")
    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__backup_output(self, init_mock, copy_mock):
        @static_var("exist_counter", 0)
        def mocked_exists(self):
            mocked_exists.exist_counter += 1
            if mocked_exists.exist_counter < 5:
                return True
            else:
                return False
        self._print_func_name()
        expected = os.path.join(TEST_DATA_DIR, "RBC.ledger.bak5")
        with patch.object(os.path, "exists", mocked_exists):
            obj = self._get_myledgerpal_obj()
            backup = obj._backup_output()
            self.assertEqual(expected, backup)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_columns(self, init_mock):
        self._print_func_name()
        testbank = self._get_bank_definition()
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertTrue(all(k in testbank for k in obj._columns.keys()))

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_columns_missing_field(self, init_mock):
        self._print_func_name()
        testbank = self._get_bank_definition()
        testbank.pop(mylpl.MyLedgerPal.BANK_COLNAME_DATE)
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            with self.assertRaises(Exception) as exception_ctx:
                obj = self._get_myledgerpal_obj()
                obj._initialize_bank()
            self.assertEqual("Column 'date' is not defined for bank 'RBC'",
                             exception_ctx.exception.message)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_no_encoding(self, init_mock):
        self._print_func_name()
        testbank = self._get_bank_definition()
        testbank.pop(mylpl.MyLedgerPal.BANK_ENCODING)
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertFalse(obj._encoding)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_with_encoding(self, init_mock):
        self._print_func_name()
        testbank = self._get_bank_definition()
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual("utf-8", obj._encoding)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_no_quotechar(self, init_mock):
        self._print_func_name()
        testbank = self._get_bank_definition()
        testbank.pop(mylpl.MyLedgerPal.BANK_QUOTE_CHAR)
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual('"', obj._quotechar)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_with_quotechar(self, init_mock):
        self._print_func_name()
        testbank = self._get_bank_definition()
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual("'", obj._quotechar)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_no_delimiter(self, init_mock):
        self._print_func_name()
        testbank = self._get_bank_definition()
        testbank.pop(mylpl.MyLedgerPal.BANK_DELIMITER)
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual(",", obj._delimiter)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_with_delimiter(self, init_mock):
        self._print_func_name()
        testbank = self._get_bank_definition()
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual(":", obj._delimiter)

    # Functional Tests
    # ------------------------------------------------------------------------

    def test_display_banklist(self):
        self._print_func_name(functest=True)
        p = self._spawn_process(["python", MYPL_SCRIPT, "-l"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue("Available banks" in out)

    def test_display_help(self):
        self._print_func_name(functest=True)
        p = self._spawn_process(["python", MYPL_SCRIPT, "-h"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue("mypl" in out)

    def test_unknown_bank(self):
        self._print_func_name(functest=True)
        b = "ubank"
        p = self._spawn_process(["python", MYPL_SCRIPT, b, "dummy_input"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue(mylpl.ERR_BANK_UNKNOWN.format(b) in out)

    def test_unknown_input(self):
        self._print_func_name(functest=True)
        p = self._spawn_process(
            ["python", MYPL_SCRIPT, "RBC", "invalid_input"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue(mylpl.ERR_INPUT_UNKNOWN in out)

    def test_bank_valid_but_no_input(self):
        self._print_func_name(functest=True)
        p = self._spawn_process(["python", MYPL_SCRIPT, "RBC"])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue("Usage:" in err)

    def test_backup_output(self):
        self._print_func_name(functest=True)
        input = os.path.join(TEST_DATA_DIR, "RBC.csv")
        expected = os.path.join(TEST_DATA_DIR, "RBC.ledger.bak1")
        # be sure the backup file does not exist
        if os.path.exists(expected):
            os.remove(expected)
        p = self._spawn_process(["python", MYPL_SCRIPT, "RBC", input])
        out, err = p.communicate()
        print out
        print err
        self.assertTrue(os.path.exists(expected))
        if os.path.exists(expected):
            os.remove(expected)

    def test_run(self):
        self._print_func_name(functest=True)
        input = os.path.join(TEST_DATA_DIR, "RBC.csv")
        output = os.path.join(TEST_DATA_DIR, "RBC.ledger")
        app = mylpl.MyLedgerPal('RBC', input, output)
        app.run()


if __name__ == '__main__':
    unittest.main()
