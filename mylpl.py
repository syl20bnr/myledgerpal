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
import re
import csv


ERR_BANK_UNKNOWN = "Unknown bank '{0}'"
ERR_INPUT_UNKNOWN = "Prodived input file does not exist."
ERR_UNDEFINED_COLUMN = "Column '{0}' is not defined for bank '{1}'"


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
    except Exception as e:
        if args['--debug']:
            import traceback
            print traceback.format_exc()
        else:
            print("Error: {0}".format(str(e)))


class MyLedgerPal(object):

    BANKS_COLNAME_ACC_NUM = 'acc_num'
    BANKS_COLNAME_DATE = 'date'
    BANKS_COLNAME_CHECK_NUM = 'check_num'
    BANKS_COLNAME_DESC = 'desc'
    BANKS_COLNAME_AMOUNT = 'amount'

    BANKS = {
        'RBC': {BANKS_COLNAME_ACC_NUM: 1,
                BANKS_COLNAME_DATE: 2,
                BANKS_COLNAME_CHECK_NUM: 3,
                BANKS_COLNAME_DESC: [4, 5],
                BANKS_COLNAME_AMOUNT: 6}}

    @staticmethod
    def print_banks():
        print(MyLedgerPal._get_bank_helplist())

    @staticmethod
    def _get_bank_helplist():
        l = ["Available banks:"]
        for n in MyLedgerPal.BANKS:
            l.append(n)
        return os.linesep.join(l)

    def __init__(self, bank, input, output):
        self._bank = bank
        self._input = input
        self._output = output
        self._columns = {}
        self._initialize_params()

    def _initialize_params(self):
        if self._bank not in MyLedgerPal.BANKS:
            raise Exception(ERR_BANK_UNKNOWN.format(self._bank))
        if not os.path.exists(self._input):
            raise Exception(ERR_INPUT_UNKNOWN)
        self._initialize_bank()
        if os.path.exists(self._output):
            self._backup_output()

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
            os.path.dirname(backup)
        ))
        return backup

    def _get_bank_colidx_definition(self, bankname):
        return MyLedgerPal.BANKS[bankname]

    def _initialize_bank(self):
        c = MyLedgerPal
        i = self._get_bank_colidx_definition(self._bank)
        self._columns[c.BANKS_COLNAME_ACC_NUM] = i.get(
            c.BANKS_COLNAME_ACC_NUM, -1)
        self._columns[c.BANKS_COLNAME_CHECK_NUM] = i.get(
            c.BANKS_COLNAME_CHECK_NUM, -1)
        self._columns[c.BANKS_COLNAME_AMOUNT] = i.get(
            c.BANKS_COLNAME_AMOUNT, -1)
        self._columns[c.BANKS_COLNAME_DESC] = i.get(c.BANKS_COLNAME_DESC, -1)
        self._columns[c.BANKS_COLNAME_DATE] = i.get(c.BANKS_COLNAME_DATE, -1)
        # for now we don't allow undefined field
        for k, v in self._columns.items():
            if v == -1:
                raise Exception(ERR_UNDEFINED_COLUMN.format(k, self._bank))


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


# def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
#     # csv.py doesn't do Unicode; encode temporarily as UTF-8:
#     csv_reader = csv.reader(unicode_csv_data, dialect=dialect, **kwargs)
#     for row in csv_reader:
#         # decode UTF-8 back to Unicode, cell by cell:
#         yield [unicode(cell, 'utf-8') for cell in row]

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
