# PREBOORU.PY

# ## PYTHON IMPORTS
import os
from argparse import ArgumentParser

# ## LOCAL IMPORTS
from app.logical.file import LoadDefault, PutGetJSON
from app.config import workingdirectory, datafilepath

# ## GLOBAL VARIABLES

PID_FILENAME_FORMAT = workingdirectory + datafilepath + '%s-server-pid.json'
SERVER_NAMES = ['prebooru', 'worker', 'similarity'] # NGINX, ...

SERVER_ARGS = {
    'prebooru': "",
    'worker': "",
    'similarity': "server",
}


# ## FUNCTIONS

# #### Auxiliary functions


def StartServer(name, keepopen):
    print("Starting %s" % name)
    if keepopen:
        os.system('start cmd.exe /K "python %s.py --title %s"' % (name, SERVER_ARGS[name]))
    else:
        os.system('start python %s.py --title %s' % (name, SERVER_ARGS[name]))


def StopServer(name, *args):
    filename = PID_FILENAME_FORMAT % name
    pid = next(iter(LoadDefault(filename, [])), None)
    if pid is not None:
        print("Killing %s: %d" % (name, pid))
        os.system('taskkill /PID %d /F' % pid)
        PutGetJSON(filename, 'w', [])
    else:
        print("Server %s not running." % name)


# #### Main execution functions


def StartAll(*args):
    for name in SERVER_NAMES:
        StartServer(name, False)


def StopAll(*args):
    for name in SERVER_NAMES:
        StopServer(name)


# #### Main function


def Main(args):
    if (args.operation in ['start', 'stop']) and (args.type not in SERVER_NAMES):
        print("Must select a valid server name to %s: %s" % (args.operation, ', '.join(SERVER_NAMES)))
        exit(-1)
    switcher = {
        'startall': StartAll,
        'stopall': StopAll,
        'start': StartServer,
        'stop': StopServer,
    }
    switcher[args.operation](args.type, args.keepopen)

# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Server to process network requests.")
    parser.add_argument('operation', choices=['startall', 'stopall', 'start', 'stop'])
    parser.add_argument('--keepopen', required=False, default=False, action="store_true")
    parser.add_argument('--type', type=str, required=False)
    args = parser.parse_args()
    Main(args)
