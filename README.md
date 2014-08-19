# My Ledger Pal

__This is a Work In Progress__


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
