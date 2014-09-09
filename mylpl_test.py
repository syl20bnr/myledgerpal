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

    def _get_resources_data(self):
        return {"accounts": {"000-000-0000": {"account": "Assets:Acc1",
                                              "currency": "CAD"},
                             "111-111-1111": {"account": "Liabilites:Acc2",
                                              "currency": "USD"}},
                "aliases": {"SRC1": "Source1",
                            "SRC2": "Source2",
                            "SRC3": "Source3"},
                "rules": {"Expenses:num1": {"Source1": 100, "Source2": 100},
                          "Expenses:num2": {"Source3": 40},
                          "Expenses:num3": {"Source3": 60}}}

    def _get_resources_data_no_account(self):
        res = self._get_resources_data()
        res.pop("accounts")
        return res

    def _get_resources_data_no_ledger_account(self):
        res = self._get_resources_data()
        res["accounts"]["000-000-0000"].pop("account")
        res["accounts"]["111-111-1111"].pop("account")
        return res

    def _get_resources_data_no_currency(self):
        res = self._get_resources_data()
        res["accounts"]["000-000-0000"].pop("currency")
        res["accounts"]["111-111-1111"].pop("currency")
        return res

    def _get_resources_data_no_alias(self):
        res = self._get_resources_data()
        res.pop("aliases")
        return res

    def _get_resources_data_no_rule(self):
        res = self._get_resources_data()
        res.pop("rules")
        return res

    # Unit Tests
    # ------------------------------------------------------------------------

    @patch.object(shutil, "copyfile")
    @patch.object(mylpl.MyLedgerPal, "_print_backup_msg")
    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__backup_output(self, init_mock, print_mock, copy_mock):
        @static_var("exist_counter", 0)
        def mocked_exists(self):
            mocked_exists.exist_counter += 1
            if mocked_exists.exist_counter < 5:
                return True
            else:
                return False
        expected = os.path.join(TEST_DATA_DIR, "RBC.ledger.bak5")
        with patch.object(os.path, "exists", mocked_exists):
            obj = self._get_myledgerpal_obj()
            backup = obj._backup_output()
            self.assertEqual(expected, backup)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_columns(self, init_mock):
        testbank = self._get_bank_definition()
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertTrue(all(k in testbank for k in obj._columns.keys()))

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_columns_missing_field(self, init_mock):
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
        testbank = self._get_bank_definition()
        testbank.pop(mylpl.MyLedgerPal.BANK_ENCODING)
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertFalse(obj._encoding)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_with_encoding(self, init_mock):
        testbank = self._get_bank_definition()
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual("utf-8", obj._encoding)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_no_quotechar(self, init_mock):
        testbank = self._get_bank_definition()
        testbank.pop(mylpl.MyLedgerPal.BANK_QUOTE_CHAR)
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual('"', obj._quotechar)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_with_quotechar(self, init_mock):
        testbank = self._get_bank_definition()
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual("'", obj._quotechar)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_no_delimiter(self, init_mock):
        testbank = self._get_bank_definition()
        testbank.pop(mylpl.MyLedgerPal.BANK_DELIMITER)
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual(",", obj._delimiter)

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__initialize_bank_with_delimiter(self, init_mock):
        testbank = self._get_bank_definition()
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual(":", obj._delimiter)

    # ------------------------ Resources -----------------------------

    def test_resource_load_with_accounts_in_data(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual(2, res.get_account_count())

    def test_resource_load_no_account_in_data(
            self):
        dct = self._get_resources_data_no_account()
        res = mylpl.Resources.load(dct)
        self.assertEqual(0, res.get_account_count())

    def test_resource_get_ledger_account_in_data(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual("Assets:Acc1", res.get_ledger_account("000-000-0000"))
        self.assertEqual("Liabilites:Acc2",
                         res.get_ledger_account("111-111-1111"))

    def test_resource_get_ledger_account_no_account_in_data(self):
        dct = self._get_resources_data_no_account()
        res = mylpl.Resources.load(dct)
        self.assertEqual(
            "000-000-0000", res.get_ledger_account("000-000-0000"))
        self.assertEqual(
            "111-111-1111", res.get_ledger_account("111-111-1111"))

    def test_resource_get_ledger_account_no_ledger_account_in_data(self):
        dct = self._get_resources_data_no_ledger_account()
        res = mylpl.Resources.load(dct)
        self.assertEqual(
            "000-000-0000", res.get_ledger_account("000-000-0000"))
        self.assertEqual(
            "111-111-1111", res.get_ledger_account("111-111-1111"))

    def test_resource_get_ledger_account_get_currency(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual("CAD", res.get_currency("000-000-0000"))
        self.assertEqual("USD", res.get_currency("111-111-1111"))

    def test_resource_get_ledger_account_get_currency_no_account_in_data(self):
        dct = self._get_resources_data_no_account()
        res = mylpl.Resources.load(dct)
        self.assertEqual("$", res.get_currency("000-000-0000"))
        self.assertEqual("$", res.get_currency("111-111-1111"))

    def test_resource_get_ledger_account_get_currency_no_currency_in_data(
            self):
        dct = self._get_resources_data_no_currency()
        res = mylpl.Resources.load(dct)
        self.assertEqual("$", res.get_currency("000-000-0000"))
        self.assertEqual("$", res.get_currency("111-111-1111"))

    def test_resource_load_with_aliases_in_data(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual(3, res.get_alias_count())

    def test_resource_load_with_no_alias_in_data(self):
        dct = self._get_resources_data_no_alias()
        res = mylpl.Resources.load(dct)
        self.assertEqual(0, res.get_alias_count())

    def test_resource_get_aliases_with_aliases_in_data(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual("Source1", res.get_alias("SRC1"))
        self.assertEqual("Source2", res.get_alias("SRC2"))
        self.assertEqual("Source3", res.get_alias("SRC3"))

    def test_resource_get_aliases_with_no_alias_in_data(self):
        dct = self._get_resources_data_no_alias()
        res = mylpl.Resources.load(dct)
        self.assertEqual("SRC1", res.get_alias("SRC1"))
        self.assertEqual("SRC2", res.get_alias("SRC2"))
        self.assertEqual("SRC3", res.get_alias("SRC3"))

    def test_resource_load_with_rules_in_data(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual(3, res.get_rule_count())

    def test_resource_load_with_no_rule_in_data(self):
        dct = self._get_resources_data_no_rule()
        res = mylpl.Resources.load(dct)
        self.assertEqual(0, res.get_rule_count())

    def test_resource_get_rules_with_rules_in_data(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual(
            {"Source1": {"Expenses:num1": 100},
             "Source2": {"Expenses:num1": 100},
             "Source3": {"Expenses:num2": 40, "Expenses:num3": 60}},
            res.get_rules())

    def test_resource_get_rules_with_no_rule_in_data(self):
        dct = self._get_resources_data_no_rule()
        res = mylpl.Resources.load(dct)
        self.assertEqual({}, res.get_rules())

    def test_resource_get_payee(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual("Source1", res.get_payee("SRC1"))
        self.assertEqual("Source2", res.get_payee("SRC2"))
        self.assertEqual("Source3", res.get_payee("SRC3"))

    def test_resource_get_payee_with_no_alias(self):
        dct = self._get_resources_data_no_alias()
        res = mylpl.Resources.load(dct)
        self.assertEqual("SRC1", res.get_payee("SRC1"))
        self.assertEqual("SRC2", res.get_payee("SRC2"))
        self.assertEqual("SRC3", res.get_payee("SRC3"))
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

    # def test_backup_output(self):
    #     self._print_func_name(functest=True)
    #     input = os.path.join(TEST_DATA_DIR, "RBC.csv")
    #     output = os.path.join(TEST_DATA_DIR, "RBC.ledger")
    #     expected = os.path.join(TEST_DATA_DIR, "RBC.ledger.bak1")
    #     # be sure the backup file does not exist
    #     if os.path.exists(expected):
    #         os.remove(expected)
    #     p = self._spawn_process(["python", MYPL_SCRIPT, "RBC", input])
    #     out, err = p.communicate()
    #     print out
    #     print err
    #     self.assertTrue(os.path.exists(expected))
    #     with open(output, 'r') as o:
    #         with open(expected, 'r') as e:
    #             self.assertEqual(o.read(), e.read())
    #     if os.path.exists(expected):
    #         os.remove(expected)

    # def test_load_resource(self):
    #     self._print_func_name(functest=True)
    #     input = os.path.join(TEST_DATA_DIR, "RBC.csv")
    #     output = os.path.join(TEST_DATA_DIR, "RBC.ledger")
    #     app = mylpl.MyLedgerPal('RBC', input, output)
    #     self.assertEqual(2, app._resources.get_account_count())
    #     self.assertEqual(4, app._resources.get_alias_count())
    #     self.assertEqual(3, app._resources.get_rule_count())

    # def test_run(self):
    #     self._print_func_name(functest=True)
    #     input = os.path.join(TEST_DATA_DIR, "RBC.csv")
    #     output = os.path.join(TEST_DATA_DIR, "RBC.ledger")
    #     app = mylpl.MyLedgerPal('RBC', input, output)
    #     app.run()


if __name__ == '__main__':
    unittest.main()
