import sys
import logging
from pprint import pformat

logging.basicConfig(filename='/tmp/listener.log', level=logging.DEBUG,
                    format='%(name)s %(message)s')
log = logging.getLogger('listener')

def write_stdout(s):
    sys.stdout.write(s)
    sys.stdout.flush()

def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()

def main():
    while 1:
        write_stdout('READY\n') # transition from ACKNOWLEDGED to READY
        line = sys.stdin.readline()  # read header line from stdin
        write_stderr(line) # print it out to stderr
        headers = dict([ x.split(':') for x in line.split() ])
        log.debug('headers: ' + pformat(headers))
        data = sys.stdin.read(int(headers['len'])) # read the event payload
        log_data = dict([ x.split(':') for x in data.split() ])
        write_stderr(data) # print the event payload to stderr
        log.debug('data: ' + pformat(log_data) + '\n##################')
        write_stdout('RESULT 2\nOK') # transition from READY to ACKNOWLEDGED

if __name__ == '__main__':
    main()
    import sys
