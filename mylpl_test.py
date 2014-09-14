# -*- coding: utf-8 -*-
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

    def _get_resources_data_rule_percentage_sum_is_not_100(self):
        res = self._get_resources_data()
        res["rules"] = {"Expenses:num1": {"Source1": 30, "Source2": 10}}
        return res

    def _get_post(self):
        return mylpl.Post({"Assets:MyAccount": 100},
                          "$",
                          "9/9/9999",
                          "01",
                          "Payee",
                          {"Expenses:Payee": 100},
                          -100)


    def _get_post_several_payee_accounts_sum_under_100(self):
        post = self._get_post()
        post._payee_accounts = {"Expenses:Payee1": 20,
                                "Expenses:Payee2": 45}
        return post

    def _get_post_several_payee_accounts_sum_above_100(self):
        post = self._get_post()
        post._payee_accounts = {"Expenses:Payee1": 20,
                                "Expenses:Payee2": 85}
        return post
    # Unit Tests
    # ------------------------------------------------------------------------

    # ------------------------ MyLedgerPal -----------------------------

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

    @patch.object(mylpl.MyLedgerPal, "_initialize_params")
    def test__get_row_data_bank_rbc(self, init_mock):
        row1 = [u"Chèques",
                u"00335-1234567",
                u"5/5/2014",
                u"",
                u"VERSEMENT SUR HYP", u"",
                u"-756.38", "", ""]
        row2 = [u"Chèques",
                u"00335-1234567",
                u"5/5/2014",
                u"",
                u"VERSEMENT SUR HYP", u"OTHEQUE",
                u"-756.38", "", ""]
        testbank = self._get_bank_definition()
        with patch.object(mylpl.MyLedgerPal, "_get_bank_colidx_definition",
                          return_value=testbank):
            obj = self._get_myledgerpal_obj()
            obj._initialize_bank()
            self.assertEqual(u"00335-1234567", obj._get_row_data(
                row1, mylpl.MyLedgerPal.BANK_COLNAME_ACC_NUM))
            self.assertEqual(u"5/5/2014", obj._get_row_data(
                row1, mylpl.MyLedgerPal.BANK_COLNAME_DATE))
            self.assertEqual(u"VERSEMENT SUR HYP", obj._get_row_data(
                row1, mylpl.MyLedgerPal.BANK_COLNAME_DESC))
            self.assertEqual(u"VERSEMENT SUR HYP OTHEQUE", obj._get_row_data(
                row2, mylpl.MyLedgerPal.BANK_COLNAME_DESC))
            self.assertEqual(u"", obj._get_row_data(
                row1, mylpl.MyLedgerPal.BANK_COLNAME_CHECK_NUM))
            self.assertEqual(u"-756.38", obj._get_row_data(
                row1, mylpl.MyLedgerPal.BANK_COLNAME_AMOUNT))

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
        self.assertEqual({"Assets:Acc1": 100},
                         res.get_ledger_account("000-000-0000"))

    def test_resource_get_ledger_account_no_account_in_data(self):
        dct = self._get_resources_data_no_account()
        res = mylpl.Resources.load(dct)
        self.assertEqual({"Assets:000-000-0000": 100},
                         res.get_ledger_account("000-000-0000"))

    def test_resource_get_ledger_account_no_ledger_account_in_data(self):
        dct = self._get_resources_data_no_ledger_account()
        res = mylpl.Resources.load(dct)
        self.assertEqual({"Assets:000-000-0000": 100},
                         res.get_ledger_account("000-000-0000"))

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

    def test_resource_with_rule_percentage_sum_equal_to_100(self):
        dct = self._get_resources_data()
        mylpl.Resources.load(dct)

    def test_resource_with_rule_percentage_sum_not_equal_to_100(self):
        dct = self._get_resources_data_rule_percentage_sum_is_not_100()
        with self.assertRaises(Exception) as exception_ctx:
            mylpl.Resources.load(dct)
        self.assertEqual(mylpl.ERR_PERCENTAGE_SUM_NOT_EQUAL_TO_100,
                         exception_ctx.exception.message)

    def test_resource_get_payee(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual("Source1", res.get_payee("SRC1"))
        self.assertEqual("Source2", res.get_payee("SRC2"))
        self.assertEqual("Source3", res.get_payee("SRC3"))

    def test_resource_get_payee_with_no_alias_in_data(self):
        dct = self._get_resources_data_no_alias()
        res = mylpl.Resources.load(dct)
        self.assertEqual("SRC1", res.get_payee("SRC1"))
        self.assertEqual("SRC2", res.get_payee("SRC2"))
        self.assertEqual("SRC3", res.get_payee("SRC3"))

    def test_resource_get_payee_account(self):
        dct = self._get_resources_data()
        res = mylpl.Resources.load(dct)
        self.assertEqual({"Expenses:num1": 100},
                         res.get_payee_account("Source1"))
        self.assertEqual({"Expenses:num1": 100},
                         res.get_payee_account("Source2"))
        self.assertEqual({"Expenses:num2": 40, "Expenses:num3": 60},
                         res.get_payee_account("Source3"))

    def test_resource_get_payee_account_with_no_rule_in_data(self):
        dct = self._get_resources_data_no_rule()
        res = mylpl.Resources.load(dct)
        self.assertEqual({"Expenses:Unknown": 100},
                         res.get_payee_account("Source1"))
        self.assertEqual({"Expenses:Unknown": 100},
                         res.get_payee_account("Source2"))
        self.assertEqual({"Expenses:Unknown": 100},
                         res.get_payee_account("Source3"))

    # ------------------------ Post -----------------------------

    def test_post__get_adjusted_amount_positive_100(self):
        self.assertEqual("50.00", mylpl.Post._get_adjusted_amount(100, 50))

    def test_post__get_adjusted_amount_0(self):
        self.assertEqual("0.00", mylpl.Post._get_adjusted_amount(100, 0))

    def test_post__get_adjusted_amount_negative_100(self):
        self.assertEqual("50.00", mylpl.Post._get_adjusted_amount(-100, 50))

    def test_post__format_amount_dollar(self):
        self.assertEqual("$ 25.00", mylpl.Post._format_amount(-50, 50, "$"))

    def test_post__format_amount_usd(self):
        self.assertEqual("10.00 USD", mylpl.Post._format_amount(200, 5, "USD"))

    def test_post__compute_amount_alignment(self):
        post = self._get_post()
        res = post._compute_amount_alignment("Expenses:Payee", 100)
        self.assertEqual(36, res)

    def test_post__compute_amount_alignment_negative_amount(self):
        post = self._get_post()
        post._amount = -100
        res = post._compute_amount_alignment("Expenses:Payee", 50)
        self.assertEqual(37, res)

    def test_post__compute_amount_alignment_cad(self):
        post = self._get_post()
        post._currency = "CAD"
        res = post._compute_amount_alignment("Expenses:Payee", 50)
        self.assertEqual(35, res)

    def test_post__format_payee_accounts_negative_amount(self):
        post = self._get_post()
        self.assertEqual(u"    Expenses:Payee             "
                         u"                       $ 100.00",
                         post._format_payee_accounts())

    def test_post__format_payee_accounts_positive_amount(self):
        post = self._get_post()
        post._amount = abs(post._amount)
        self.assertEqual("    Assets:MyAccount           "
                         "                       $ 100.00",
                         post._format_payee_accounts())

    def test_post__format_balance_account_negative_amount(self):
        post = self._get_post()
        self.assertEqual(u"    Assets:MyAccount",
                         post._format_balance_account())

    def test_post__format_balance_account_positive_amount(self):
        post = self._get_post()
        post._amount = abs(post._amount)
        self.assertEqual(u"    Expenses:Payee",
                         post._format_balance_account())

    def test__validate_ok(self):
        post = self._get_post()
        post._validate()

    def test__validate_payee_accounts_percentage_sum_not_equal_to_100(self):
        post = self._get_post_several_payee_accounts_sum_under_100()
        with self.assertRaises(Exception) as exception_ctx:
            post._validate()
        self.assertEqual(mylpl.ERR_PERCENTAGE_SUM_NOT_EQUAL_TO_100,
                         exception_ctx.exception.message)

    def test_post___str__(self):
        post = self._get_post()
        self.assertEqual(
            u"\n"
            u"9/9/9999 * Payee\n"
            u"    Expenses:Payee                                    $ 100.00\n"
            u"    Assets:MyAccount\n",
            unicode(post))

    def test_post___str___several_payee_accounts_sum_under_100(self):
        post = self._get_post_several_payee_accounts_sum_under_100()
        with self.assertRaises(Exception) as exception_ctx:
            unicode(post)
        self.assertEqual(mylpl.ERR_PERCENTAGE_SUM_NOT_EQUAL_TO_100,
                         exception_ctx.exception.message)

    def test_post___str___several_payee_accounts_sum_above_100(self):
        post = self._get_post_several_payee_accounts_sum_above_100()
        with self.assertRaises(Exception) as exception_ctx:
            unicode(post)
        self.assertEqual(mylpl.ERR_PERCENTAGE_SUM_NOT_EQUAL_TO_100,
                         exception_ctx.exception.message)

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

    def test_run(self):
        self._print_func_name(functest=True)
        input = os.path.join(TEST_DATA_DIR, "RBC.csv")
        output = os.path.join(TEST_DATA_DIR, "RBC.ledger")
        app = mylpl.MyLedgerPal('RBC', input, output)
        app.run()


if __name__ == '__main__':
    unittest.main()
