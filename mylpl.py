#!/bin/env python
# -*- coding: utf-8 -*-
'''mypl.py (2014 - Sylvain Benner)
My ledger pal helps me to import CSV reports produced by my bank.

Usage:
  mypl.py <bank> <input> [-o OUTPUT] [-i --interactive] [-d --debug]
  mypl.py (-l | --list) [-d --debug]
  mypl.py (-h | --help)
  mypl.py --version

Options:
  <bank>            My bank.
  <input>           Input CSV file.
  -d --debug        Print callstack.
  -h --help         Show this help.
  -i --interactive  Will ask me for information about the posts before
                    writing them to my ledger file.
  -l --list         List the available banks.
  -o OUTPUT         My ledger file where to export the posts.
  --version         Show version.

Github repo: https://github.com/syl20bnr/myledgerpal
'''
from docopt import docopt
import os
import shutil
import csv
import json
# import re


ERR_BANK_UNKNOWN = "Unknown bank '{0}'"
ERR_INPUT_UNKNOWN = "Prodived input file does not exist."
ERR_UNDEFINED_COLUMN = "Column '{0}' is not defined for bank '{1}'"

RESOURCES_FILENAME = ".mylplrc"


def main():
    try:
        args = docopt(__doc__, version='My Ledger Pal (mylpl) v0.1')
        if args['--list']:
            MyLedgerPal.print_banks()
        else:
            o = ""
            if args['-o']:
                o = os.path.abspath(os.path.normpath(args['-o']))
            else:
                o = os.path.splitext(args['<input>'])[0] + '.ledger'
            i = os.path.abspath(os.path.normpath(args['<input>']))
            app = MyLedgerPal(args['<bank>'], i, o)
            app.run
    except Exception as e:
        if args['--debug']:
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

    BANKS = {
        'RBC': {BANK_ENCODING: "ISO-8859-1",
                BANK_QUOTE_CHAR: '"',
                BANK_DELIMITER: ",",
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
        return [os.path.join(loc, RESOURCES_FILENAME) for loc in locs]

    def __init__(self, bank, input, output):
        self._bank = bank
        self._input = input
        self._output = output
        self._columns = {}
        self._encoding = ""
        self._quotechar = '"'
        self._delimiter = ","
        self._resources = None
        self._initialize_params()

    def _initialize_params(self):
        # error checks
        if self._bank not in MyLedgerPal.BANKS:
            raise Exception(ERR_BANK_UNKNOWN.format(self._bank))
        if not os.path.exists(self._input):
            raise Exception(ERR_INPUT_UNKNOWN)
        # more initializations
        self._initialize_bank()
        self._load_resources()
        # additional behavior
        if os.path.exists(self._output):
            self._backup_output()

    def _initialize_bank(self):
        c = MyLedgerPal
        i = self._get_bank_colidx_definition(self._bank)
        self._encoding = i.get(c.BANK_ENCODING, "")
        self._quotechar = i.get(c.BANK_QUOTE_CHAR, '"')
        self._delimiter = i.get(c.BANK_DELIMITER, ",")
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
            self._resources = Resources.load(json.loads(data))

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
        print("Backup file '{0}' has been created in {1}.".format(
            os.path.basename(backup),
            os.path.dirname(backup)))
        return backup

    def _get_bank_colidx_definition(self, bankname):
        return MyLedgerPal.BANKS[bankname]

    def _csv_reader(self, data, dialect=csv.excel, **kwargs):
        # csv.py doesn't do Unicode; encode temporarily as UTF-8:
        csv_reader = csv.reader(data, dialect=dialect, **kwargs)
        for row in csv_reader:
            # decode UTF-8 back to Unicode, cell by cell:
            if self._encoding:
                yield [unicode(cell, self._encoding) for cell in row]
            else:
                yield [cell for cell in row]

    def run(self):
        with open(self._output, 'a') as o:
            with open(self._input, 'rb') as i:
                self._run(i, o)

    def _run(self, ictx, octx):
        # write directives
        octx.write('; -*- ledger -*-\n\n')
        # write entries
        reader = self._csv_reader(
            ictx, delimiter=self._delimiter, quotechar=self._quotechar)
        # skip header
        reader.next()
        posts = [self._create_post(row).write(octx) for row in reader]
        print("Number of posts: {0}".format(len(posts)))

    def _get_row_data(self, row, colname):
        if type(self._columns[colname]) is list:
            res = ""
            for i in self._columns[colname]:
                res += row[i]
            return res
        else:
            return row[self._columns[colname]]

    def _create_post(self, row):
        accountnum = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_ACC_NUM)
        date = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_DATE)
        checknum = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_CHECK_NUM)
        desc = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_DESC)
        amount = self._get_row_data(row, MyLedgerPal.BANK_COLNAME_AMOUNT)
        return Post(accountnum, date, checknum, desc, amount, self)


class Post(object):

    POST_ACCOUNT_ALIGNMENT = ' '*4
    POST_AMOUNT_ALIGNMENT = 62

    def __init__(self, accountnum, date, checknum, desc, amount, app):
        self._anum = accountnum
        self._account = 'account'
        self._date = date
        self._cnum = checknum
        self._payee = desc
        self._amount = amount.replace("-", "")
        self._comment = ""
        self._is_income = '-' not in amount
        self._category = "toto"
        self._app = app

    def write(self, octx):
        post = ''
        if self._is_income:
            post = self._account
        else:
            post = u'Expenses:{0}'.format(self._category)
        a = self._compute_amount_alignment(post)
        o = unicode(
            '\n'
            '{0} * {1}{2}\n'
            '{3}{4}{5}{6}\n').format(
                self._date, self._payee, self._comment,
                Post.POST_ACCOUNT_ALIGNMENT, post, ' '*a, self._amount)
        if self._is_income:
            prefix = '' if self._category.startswith('Assets') else 'Income:'
            o += u'{0}{1}\n'.format(Post.POST_ACCOUNT_ALIGNMENT,
                                    u'{0}{1}'.format(prefix, self._category))
        if self._app._encoding:
            octx.write(o.encode(self._app._encoding))
        else:
            octx.write(o)

    def _compute_amount_alignment(self, c):
        lacc = len(Post.POST_ACCOUNT_ALIGNMENT + c)
        lamount = len(self._amount)
        spacing = Post.POST_AMOUNT_ALIGNMENT - (lacc + lamount)
        return spacing if spacing > 0 else 1


class Resources(object):

    def __init__(self, accounts, aliases, rules):
        self._accounts = accounts
        self._aliases = aliases
        self._rules = rules

    @staticmethod
    def load(dct):
        accounts = dct["accounts"]
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
        rules = dct["rules"]
        rev_rules = {}
        for k, v in rules.items():
            for k1, v1 in v.items():
                rev_rules[k1] = rev_rules.get(k1, {})
                rev_rules[k1][k] = v1
        return Resources(accounts, dct["aliases"], rev_rules)

    def get_accounts(self):
        return self._accounts

    def get_account_count(self):
        return len(self._accounts)

    def get_ledger_account(self, accnumber):
        ''' Note, the account number must be passed as a string. '''
        return self._accounts[accnumber]["account"]

    def get_currency(self, accnumber):
        ''' Note, the account number must be passed as a string. '''
        return self._accounts[accnumber]["currency"]

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


# class Entry(object):

#     cat_regexps = {
#         re.compile(u'Aménagement:.*'): u'Aménagement',
#         re.compile(u'Équipements:.*'): u'Équipements',
#         re.compile(u'Revenus:'): u'',
#         re.compile(u"Taxes et Impôts:Crédits d'impôts"): u"Crédits d'impôts",
#         re.compile(u"Taxes et Impôts"): u"Taxes",
#         re.compile(u'Carte de Crédit'): u'MasterCard',
#         re.compile(u'Transfert:MasterCard'): u'Assets:Compte Joint'
#     }

#     def __init__(self, row, args):
#         self._account = args['<account>']
#         self._currency = args['-c']
#         self._is_income = '-' not in row[ROW_AMOUNT]
#         self._date = row[ROW_DATE]
#         self._category = self._format_category(row[ROW_CATEGORY])
#         self._payee = row[ROW_PAYEE]
#         self._amount = self._format_amount(row[ROW_AMOUNT])
#         self._status = row[ROW_STATUS]
#         self._comment = self._format_comment(row[ROW_COMMENT])

#     def write(self, f):
#         print_verbose(u'{0} {1}'.format(self._date, self._payee))
#         target = ''
#         if self._is_income:
#             target = self._account
#         else:
#             target = u'Expenses:{0}'.format(self._category)
#         a = self._compute_amount_alignment(target)
#         o = unicode(
#             '\n'
#             '{0} * {1}{2}\n'
#             '{3}{4}{5}{6}\n').format(
#                 self._date, self._payee, self._comment,
#                 POST_ACCOUNT_ALIGNMENT, target, ' '*a, self._amount)
#         if self._is_income:
#             prefix = '' if self._category.startswith('Assets') else 'Income:'
#             o += u'{0}{1}\n'.format(POST_ACCOUNT_ALIGNMENT,
#                                     u'{0}{1}'.format(prefix, self._category))
#         f.write(o.encode('utf8'))

#     def _format_comment(self, c):
#         if c:
#             return u'\n{0}; {1}'.format(POST_ACCOUNT_ALIGNMENT, c)
#         else:
#             return u''

#     def _format_category(self, c):
#         fc = re.sub(r'.:.', ':', c)
#         for regexp, repl in Entry.cat_regexps.items():
#             fc = re.sub(regexp, repl, fc)
#         return fc

#     def _format_amount(self, a):
#         fa = a.replace('-', '').replace(',', '.').replace(unichr(160), ',')
#         if '.' not in fa:
#             fa += '.00'
#         if re.match(r'^[a-zA-Z]+$', self._currency):
#             return '{0} {1}'.format(fa, self._currency)
#         else:
#             return '{0} {1}'.format(self._currency, fa)

#     def _compute_amount_alignment(self, c):
#         lacc = len(POST_ACCOUNT_ALIGNMENT + c)
#         lamount = len(self._amount)
#         spacing = POST_AMOUNT_ALIGNMENT - (lacc + lamount)
#         return spacing if spacing > 0 else 1

    # write_header(outputfile)
    # write_posts(outputfile)
    # entries = []
    # with open(outputfile, 'w') as o:
    #     # write directives
    #     o.write('; -*- ledger -*-\n\n')
    #     o.write('bucket {0}\n'.format(args['<account>']))
    #     # write entries
    #     with open(args['<input>'], 'rb') as i:
    #         reader = unicode_csv_reader(i, delimiter=',', quotechar='"')
    #         # skip header
    #         reader.next()
    #         for row in reader:
    #             e = Entry(row, args)
    #             entries.append(e)
    #             e.write(o)
    # print_verbose('Posts found: {0}'.format(len(entries)))
    # print('Conversion has been successfully written to \"{0}\"'
    #       .format(outputfile))
