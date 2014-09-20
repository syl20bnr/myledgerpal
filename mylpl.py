#!/bin/env python
# -*- coding: utf-8 -*-
'''mypl.py (2014 - Sylvain Benner)
My ledger pal helps me to import CSV reports produced by my bank.

Usage:
  mypl.py [-dinv] <bank> <input> [-o OUTPUT]
  mypl.py (-l | --list) [-d --debug]
  mypl.py (-h | --help)
  mypl.py --version

Options:
  <bank>                  My bank.
  <input>                 Input CSV file.
  -d, --debug             Print callstack.
  -h, --help              Show this help.
  -i, --interactive       Will ask me for information about the posts before
                          writing them to my ledger file.
  -l, --list              List the available banks.
  -n, --no-backup         Will not make a backup of the output file before
                          modifying it.
  -o FILE --output FILE   My ledger file where to export the posts.
  -v, --verbose           Print more information.
  --version               Show version.

Github repo: https://github.com/syl20bnr/myledgerpal
'''
from docopt import docopt
import os
import shutil
import csv
import json
import time
import re


ERR_BANK_UNKNOWN = "Unknown bank '{0}'"
ERR_INPUT_UNKNOWN = "Prodived input file does not exist."
ERR_UNDEFINED_COLUMN = "Column '{0}' is not defined for bank '{1}'"
ERR_PERCENTAGE_SUM_NOT_EQUAL_TO_100 = "Sum of percentages is not equal to 100"
ERR_WRONG_DATE_FORMAT = "Cannot parse date {0} with respect to format {1}"


def resources_filename():
    return ".mylplrc"


def main():
    try:
        args = docopt(__doc__, version='My Ledger Pal (mylpl) v0.1')
        if args['--list']:
            MyLedgerPal.print_banks()
        else:
            o = ""
            if args['--output']:
                o = os.path.abspath(os.path.normpath(args['-o']))
            else:
                o = os.path.splitext(args['<input>'])[0] + '.ledger'
            i = os.path.abspath(os.path.normpath(args['<input>']))
            app = MyLedgerPal(args["<bank>"], i, o,
                              args["--verbose"],
                              args["--no-backup"])
            app.run()
    except Exception as e:
        if args["--debug"]:
            import traceback
            print traceback.format_exc()
        else:
            print("Error: {0}".format(str(e)))


class MyLedgerPal(object):

    BANK_COLNAME_ACC_NUM = 'acc_num'
    BANK_COLNAME_DATE = 'date'
    BANK_COLNAME_CHECK_NUM = 'check_num'
    BANK_COLNAME_DESC = 'desc'
    BANK_COLNAME_AMOUNT = 'amount'
    BANK_ENCODING = 'encoding'
    BANK_QUOTE_CHAR = 'quotechar'
    BANK_DELIMITER = 'delimiter'
    BANK_DATE_FORMAT = 'date_format'

    BANKS = {
        'RBC': {BANK_ENCODING: "ISO-8859-1",
                BANK_QUOTE_CHAR: '"',
                BANK_DELIMITER: ",",
                BANK_DATE_FORMAT: "%m/%d/%Y",
                BANK_COLNAME_ACC_NUM: 1,
                BANK_COLNAME_DATE: 2,
                BANK_COLNAME_CHECK_NUM: 3,
                BANK_COLNAME_DESC: [4, 5],
                BANK_COLNAME_AMOUNT: 6}}

    @staticmethod
    def print_banks():
        print(MyLedgerPal._get_bank_helplist())

    @staticmethod
    def _get_bank_helplist():
        l = ["Available banks:"]
        for n in MyLedgerPal.BANKS:
            l.append(n)
        return os.linesep.join(l)

    @staticmethod
    def _get_resources_file_paths(output):
        locs = [os.getcwd(), os.path.dirname(output)]
        if "HOME" in os.environ:
            locs.append(os.environ["HOME"])
        return [os.path.join(loc, resources_filename())
                for loc in locs]

    def __init__(self, bank, input, output,
                 verbose=False, no_backup=False):
        self._bank = bank
        self._input = input
        self._output = output
        self._verbose = verbose
        self._backup = not no_backup
        self._columns = {}
        self._encoding = ""
        self._quotechar = '"'
        self._delimiter = ","
        self._resources = None
        self._initialize_params()

    def run(self):
        if self._backup and os.path.exists(self._output):
            self._backup_output()
        with open(self._output, 'a') as o:
            with open(self._input, 'rb') as i:
                self._run(i, o)

    def _print(self, msg):
        if self._verbose:
            print(msg)

    def _initialize_params(self):
        # error checks
        if self._bank not in MyLedgerPal.BANKS:
            raise Exception(ERR_BANK_UNKNOWN.format(self._bank))
        if not os.path.exists(self._input):
            raise Exception(ERR_INPUT_UNKNOWN)
        # more initializations
        self._initialize_bank()
        self._resources = self._load_resources()

    def _initialize_bank(self):
        c = MyLedgerPal
        i = self._get_bank_colidx_definition(self._bank)
        self._encoding = i.get(c.BANK_ENCODING, "")
        self._quotechar = i.get(c.BANK_QUOTE_CHAR, '"')
        self._delimiter = i.get(c.BANK_DELIMITER, ",")
        self._date_format = i.get(c.BANK_DATE_FORMAT, "%Y/%m/%d")
        self._columns[c.BANK_COLNAME_ACC_NUM] = i.get(
            c.BANK_COLNAME_ACC_NUM, -1)
        self._columns[c.BANK_COLNAME_CHECK_NUM] = i.get(
            c.BANK_COLNAME_CHECK_NUM, -1)
        self._columns[c.BANK_COLNAME_AMOUNT] = i.get(
            c.BANK_COLNAME_AMOUNT, -1)
        self._columns[c.BANK_COLNAME_DESC] = i.get(c.BANK_COLNAME_DESC, -1)
        self._columns[c.BANK_COLNAME_DATE] = i.get(c.BANK_COLNAME_DATE, -1)
        # for now we don't allow undefined column indexes
        for k, v in self._columns.items():
            if v == -1:
                raise Exception(ERR_UNDEFINED_COLUMN.format(k, self._bank))

    def _load_resources(self):
        ''' Resources are loaded from these locations:
        - in the current working directory
        - beside the location of the target ledger file
        - in home
        If the file is present in different places at the same
        time then only the first encountered one will be processed.
        '''
        paths = MyLedgerPal._get_resources_file_paths(self._output)
        data = None
        i = 0
        while data is None and i < len(paths):
            data = self._get_resources_file_content(paths[i])
            i += 1
        if data:
            return Resources(json.loads(data))
        else:
            return Resources({})

    def _get_resources_file_content(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()
        else:
            return None

    def _backup_output(self):
        base = "{0}.bak".format(self._output)
        i = 1
        backup = "{0}{1}".format(base, str(i))
        while os.path.exists(backup):
            i += 1
            backup = "{0}{1}".format(base, str(i))
        shutil.copyfile(self._output, backup)
        self._print_backup_msg(backup)
        self._backup = backup

    def _print_backup_msg(self, backup):
        print("Backup file '{0}' has been created in {1}.".format(
            os.path.basename(backup),
            os.path.dirname(backup)))

    def _get_bank_colidx_definition(self, bankname):
        return MyLedgerPal.BANKS[bankname]

    def _csv_reader(self, data, dialect=csv.excel, **kwargs):
        # csv.py doesn't do Unicode; encode temporarily in the bank format
        csv_reader = csv.reader(data, dialect=dialect, **kwargs)
        while True:
            try:
                row = next(csv_reader)
                # decode back to Unicode, cell by cell:
                if self._encoding:
                    yield [unicode(cell, self._encoding) for cell in row]
                else:
                    yield [cell for cell in row]
            except csv.Error as e:
                # skip error on trailing NULL bytes
                if "NULL byte" not in e.message:
                    raise csv.Error

    def _run(self, ictx, octx):
        # write directives
        octx.write('; -*- ledger -*-\n\n')
        # write entries
        reader = self._csv_reader(
            ictx, delimiter=self._delimiter, quotechar=self._quotechar)
        # skip header
        reader.next()
        posts = [self._write_post(self._create_post(row), octx)
                 for row in reader]
        print("Number of posts: {0}".format(len(posts)))

    def _get_row_data(self, row, colname):
        if type(self._columns[colname]) is list:
            res = ""
            for i in self._columns[colname]:
                # concatenate all the columns with a space delimiter
                if res and row[i]:
                    res = " ".join([res, row[i]])
                elif row[i]:
                    res = row[i]
            return res
        else:
            return row[self._columns[colname]]

    def _get_row_date(self, row):
        date = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_DATE)
        try:
            fdate = time.strptime(date, self._date_format)
        except ValueError:
            raise Exception(ERR_WRONG_DATE_FORMAT.format(date,
                                                         self._date_format))
        return fdate

    def _create_post(self, row):
        self._print(u"Reading row: {0}".format(u",".join(row)))
        acc_num = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_ACC_NUM)
        date = self._get_row_date(row)
        checknum = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_CHECK_NUM)
        desc = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_DESC)
        payee = self._resources.get_payee(desc)
        amount = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_AMOUNT)
        return Post(self._resources.get_ledger_account(acc_num),
                    self._resources.get_currency(acc_num),
                    date,
                    checknum,
                    payee,
                    self._resources.get_payee_account(payee),
                    float(amount))

    def _write_post(self, post, octx):
        fpost = unicode(post)
        self._print(fpost)
        if self._encoding:
            octx.write(fpost.encode(self._encoding))
        else:
            octx.write(fpost)
        return post


class Post(object):

    POST_ACCOUNT_ALIGNMENT = ' '*4
    POST_AMOUNT_ALIGNMENT = 62

    @staticmethod
    def _get_adjusted_amount(amount, percent):
        return "{0:.2f}".format(abs(amount)*percent/100)

    @staticmethod
    def _format_amount(amount, percent, currency, balance=False):
        aa = Post._get_adjusted_amount(amount, percent)
        sign = "" if not balance else "-"
        if re.match(r"^[a-zA-Z]+$", currency):
            return "{0} {1}{2}".format(aa, sign, currency)
        else:
            return "{0} {1}{2}".format(currency, sign, aa)

    def __init__(self,
                 account,
                 currency,
                 date,
                 checknum,
                 payee,
                 payee_accounts,
                 amount):
        self._account = account
        self._currency = currency
        self._date = date
        self._cnum = checknum
        self._payee = payee
        self._payee_accounts = payee_accounts
        self._comment = ""
        self._amount = amount

    def _validate(self):
        percentage_sum = reduce(lambda x, y: x+y,
                                [v for v in self._payee_accounts.values()])
        if percentage_sum != 100:
            raise Exception(ERR_PERCENTAGE_SUM_NOT_EQUAL_TO_100)

    def __str__(self):
        self._validate()
        return unicode(
            '\n'
            '{0} * {1}{2}\n'
            '{3}\n'
            '{4}\n').format(self._format_date(),
                            self._payee,
                            self._comment,
                            self._format_payee_accounts(),
                            self._format_balance_account())

    def _compute_amount_alignment(self, account, percent, balance=False):
        lacc = len(Post.POST_ACCOUNT_ALIGNMENT + account)
        amount = self._amount if not balance else -self._amount
        lamount = len(Post._format_amount(amount, percent,
                                          self._currency, balance))
        spacing = Post.POST_AMOUNT_ALIGNMENT - (lacc + lamount)
        return spacing if spacing > 0 else 1

    def _format_date(self):
        return time.strftime("%Y/%m/%d", self._date)

    def _format_payee_accounts(self):
        acc = self._account if self._amount >= 0 else self._payee_accounts
        formatted = [(lambda acckey:
                      unicode("{0}{1}{2}{3}".format(
                          Post.POST_ACCOUNT_ALIGNMENT,
                          acckey,
                          ' '*self._compute_amount_alignment(acckey,
                                                             acc[acckey]),
                          Post._format_amount(self._amount, acc[acckey],
                                              self._currency))))(k)
                     for k in sorted(acc)]
        return '\n'.join(formatted)

    def _format_balance_account(self):
        acc = self._account if self._amount < 0 else self._payee_accounts
        # TODO: take into account multiple payee accounts
        formatted = unicode("{0}{1}".format(Post.POST_ACCOUNT_ALIGNMENT,
                                            acc.keys()[0]))
        if acc is self._account and 1 < len(self._payee_accounts):
            # add the balance explicitly when there are more than one payee
            # account
            formatted = unicode("{0}{1}{2}".format(
                formatted,
                ' '*self._compute_amount_alignment(acc.keys()[0], 100, True),
                Post._format_amount(-self._amount, 100, self._currency, True)))
        return formatted


class Resources(object):

    def __init__(self, dct):
        self._accounts = dct.get("accounts", {})
        self._aliases = dct.get("aliases", {})
        # we want the ledger account to be the key in the file because it
        # makes the file a lot more easier to maintain, especially because
        # it avoids a lot of redundancy. example:
        #
        # "Expenses:Alimentation:Courses": {
        #     "I G A DES SOURC": 100,
        #     "COSTCO WHOLESAL": 100
        # },
        #
        # instead of
        #
        # "I G A DES SOURC": {"Expenses:Alimentation:Courses": 100},
        # "COSTCO WHOLESAL": {"Expenses:Alimentation:Courses": 100},
        #
        # Note the ledger account which is duplicated.
        #
        # For practical reasons we want the information to be stored in memory
        # with the description as the key instead of the ledger account
        rules = dct.get("rules", {})
        self._rules = {}
        for k, v in rules.items():
            for k1, v1 in v.items():
                self._rules[k1] = self._rules.get(k1, {})
                self._rules[k1][k] = v1
        self.validate()

    def validate(self):
        for d in self._rules.values():
            percentage_sum = reduce(lambda x, y: x+y, d.values())
            if percentage_sum != 100:
                raise Exception(ERR_PERCENTAGE_SUM_NOT_EQUAL_TO_100)

    def get_accounts(self):
        return self._accounts

    def get_account_count(self):
        return len(self._accounts)

    def get_ledger_account(self, accnumber):
        ''' Note, the account number must be passed as a string. '''
        acc = ''
        if accnumber in self._accounts:
            acc = self._accounts[accnumber].get("account",
                                                'Assets:{0}'.format(accnumber))
        else:
            acc = 'Assets:{0}'.format(accnumber)
        return {acc: 100}

    def get_currency(self, accnumber):
        ''' Note, the account number must be passed as a string. '''
        if accnumber in self._accounts:
            return self._accounts[accnumber].get("currency", "$")
        else:
            return "$"

    def get_payee(self, desc):
        for k in self._aliases.keys():
            if k in desc:
                return self._aliases[k]
        return desc

    def get_payee_account(self, payee):
        for k in self._rules.keys():
            if k == payee:
                return self._rules[k]
        return {"Expenses:Unknown": 100}

    def get_aliases(self):
        return self._aliases

    def get_alias_count(self):
        return len(self._aliases)

    def get_alias(self, desc):
        return self._aliases.get(desc, desc)

    def get_rules(self):
        return self._rules

    def get_rule_count(self):
        return len(self._rules)

if __name__ == '__main__':
    main()
