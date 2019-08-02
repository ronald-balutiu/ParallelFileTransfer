import sys
import argparse
import threading
import os
from socket import *

# Globals
filesize = None
numThreads = None


class FTP:
    def __init__(self, hostname, username, password, filepath, port, logfile, threadNum):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.filepath = filepath
        self.port = port
        self.logfile = logfile
        self.threadNum = threadNum
        self.dataServer = None
        self.dataPortNo = None

    def log_handler(self, text):
        if self.logfile == '-':
            print(text)
        elif self.logfile:
            with open(self.logfile) as log:
                log.write(text)

    def SendUsername(self, control_s):
        control_s.send(('USER ' + self.username + '\r\n').encode())
        self.log_handler('C->S: ' + 'USER ' + self.username + '\r\n')

    def SendPassword(self, control_s):
        control_s.send(('PASS ' + self.password + '\r\n').encode())
        self.log_handler('C->S: ' + 'PASS ' + self.password + '\r\n')

    def SendType(self, control_s):
        control_s.send(('TYPE I' + '\r\n').encode())
        self.log_handler('C->S: ' + 'TYPE I' + '\r\n')

    def EnterPassive(self, control_s):
        control_s.send(('PASV' + '\r\n').encode())
        self.log_handler('C->S: ' + 'PASV' + '\r\n')

    ## Parses data transfer server and port no to connect to
    def AquireDataInfo(self, control_s, response):
        data_addr = ((response.decode()).split(
            '('))[1].split(')')[0].split(',')
        self.dataServer = '.'.join(data_addr[0:4])
        self.dataPortNo = int(data_addr[4]) * 256 + int(data_addr[5])
        control_s.send(('SIZE ' + self.filepath + '\r\n').encode())
        self.log_handler('C->S: ' + 'SIZE ' + self.filepath + '\r\n')

    ## Parses and returns filesize to allow for multithreading downloads
    def AquireFileSize(self, control_s, response):
        global filesize
        if not filesize:
            filesize = int((response.decode()).split(' ')[-1])
        control_s.send(('REST ' + str((filesize // numThreads)
                                      * self.threadNum) + '\r\n').encode())
        self.log_handler('C->S: ' + 'REST ' + str((filesize //
                                                   numThreads) * self.threadNum) + '\r\n')

    def RequestFile(self, control_s):
        control_s.send(('RETR ' + self.filepath + '\r\n').encode())
        self.log_handler('C->S: ' + 'RETR ' + self.filepath + '\r\n')
        self.BeginDataTransfer()

    def SendQuit(self, control_s):
        control_s.send(('QUIT' + '\r\n').encode())
        self.log_handler('C->S: ' + 'QUIT' + '\r\n')

    def Disconnect(self, control_s):
        control_s.close()
        sys.exit(0)

    def waitingFunc(self, control_s):
        pass

    # Main transfer Logic
    def BeginTransfer(self):
        control_s = socket(AF_INET, SOCK_STREAM)
        server = gethostbyname(self.hostname)
        if control_s.connect((server, self.port)):
            error_message('Cannot connect to server')
            exit(1)
        while 1:
            response = control_s.recv(4096)
            num = response[0:3].decode()
            self.log_handler('S->C: ' + response.decode())
            responseDictionary = {
                '220': self.SendUsername,
                '331': self.SendPassword,
                '230': self.SendType,
                '200': self.EnterPassive,
                '227': self.AquireDataInfo,
                '213': self.AquireFileSize,
                '350': self.RequestFile,
                '226': self.SendQuit,
                '221': self.Disconnect
            }
            if num == '221':
                quit()
            try:
                responseDictionary.get(num)(control_s)
            except:
                try:
                    responseDictionary.get(num)(control_s, response)
                except:
                    pass

    def BeginDataTransfer(self):
        data_s = socket(AF_INET, SOCK_STREAM)
        data_s.connect((self.dataServer, self.dataPortNo))
        filename = self.filepath.split('/')[-1]
        if numThreads == 1:
            filedata = open(filename, 'wb')
        else:
            filedata = open(filename + str(self.threadNum), 'wb')
        bytesWritten = 0
        if self.threadNum + 1 == numThreads:
            downloadSize = (filesize // numThreads) + numThreads
        else:
            downloadSize = filesize // numThreads
        while 1:
            data = data_s.recv(4096)
            if not data:
                break
            leftToWrite = downloadSize - bytesWritten
            if leftToWrite == 0:
                break
            if leftToWrite <= 4096:
                filedata.wrire(data[:leftToWrite - 1])
            else:
                filedata.write(data)
            bytesWritten += len(data)


def error_message(text):
    sys.stderr.write(text + '\n')


def ThreadHandler(hostname, username, password, filepath, port, logfile, i):
    thread = FTP(hostname, username, password, filepath, port, logfile, i)
    thread.BeginTransfer()


def main(argv):
    global numThreads
    global filesize

    num_argv = len(argv)
    parser = argparse.ArgumentParser(
        description='Parallel FTP Program', add_help=False)
    parser.add_argument('-h', '--help', action='store_true',
                        help=argparse._('Show this help message and exit.'))
    parser.add_argument('-v', '--version', action='store_true',
                        help='Prints name of application, version number, and author.')
    parser.add_argument('-f', '--file', type=str,
                        help='The specified file to be downloaded (including file path if needed).')
    parser.add_argument('-s', '--server', type=str,
                        help='The specified hostname to download the file from.')
    parser.add_argument('-p', '--port', type=int,
                        help='The specified port to connect to the server from. Default: 21')
    parser.add_argument('-n', '--username', type=str,
                        help='The specified username to login to server. Default: anonymous')
    parser.add_argument('-P', '--password', type=str,
                        help='The specified password to login to server. Default: user@localhost.localnet')
    parser.add_argument('-l', '--log', type=str,
                        help='The specified logfile to log all FTP communications with server. Default: No log')
    parser.add_argument('-t', '--thread', type=str,
                        help='The specified configuration file if multithreaded download is requested.')

    if argv[1] not in ['-s', '-t', '-h', '-v', '--help', '--version']:
        error_message('Syntax error in client request. Error: 4')
        sys.exit(4)
    if argv[1] == '-s' and argv[3] != '-f':
        error_message('Syntax error in client request. Error: 4')
        sys.exit(4)

    try:
        args = parser.parse_args()
    except:
        try:
            raise Exception()
        except:
            error_message(
                'Syntax error in client request. Please type -h to see correct formatting. Error: 4')
            sys.exit(4)

    if args.help:
        if num_argv == 2:
            parser.print_help()
            sys.exit(0)
        else:
            error_message(
                'Syntax error in client request. Help command cannot be paired with other args. Error: 4')
            sys.exit(4)

    if args.version:
        if num_argv == 2:
            print('PFTP, Version 0.1, By: Ronald Balutiu')
            sys.exit(0)
        else:
            error_message(
                'Syntax error in client request. Version command cannot be paired with other args. Error: 4')
            sys.exit(4)

    config = (None if not args.thread else args.thread)
    port = (21 if not args.port else args.port)
    username = ('anonymous' if not args.username else args.username)
    password = (
        'user@localhost.localnet' if not args.password else args.password)
    logfile = (None if not args.log else args.log)

    if args.server and config == None:
        hostname = args.server.split('/')
        for names in hostname:
            if '.' in names:
                hostname = names
                break

    if logfile is not None:
        if os.path.exists(logfile):
            os.remove(logfile)

    if not args.file:
        error_message('Syntax error in client request. Must specify file.')
        sys.exit(4)
    else:
        filepath = args.file

    if config:
        threadFile = open(config, 'r')
        lines = threadFile.readlines()
        numThreads = len(lines)
        i = 0
        for line in lines:
            line = line.split('@')
            username = line[0].split(':')[1].split('/')[-1]
            password = line[0].split(':')[-1]
            hostname = line[1].split('/')[0]
            filepath = line[1].split('/')
            del filepath[0]
            filepath = '/'.join(filepath).split('\n')[0]
            threadHolder[i] = threading.Thread(target=ThreadHandler, args=(
                hostname, username, password, filepath, port, logfile, i))
            threadholder[i].start()
            i += 1
        tempFileList = []
        for i in range(numThreads):
            threadHolder[i].join()
            tempFileList.append(filepath + str(i))
        with open(filepath, 'wb') as f:
            for tempFile in tempFileList:
                with open(tempFile, 'rb') as infile:
                    f.write(infile.red())
                os.remove(tempFile)
        exit(0)
    else:
        if os.path.exists(filepath):
            os.remove(filepath)
        numThreads = 1
        transferThread = FTP(hostname, username, password,
                             filepath, port, logfile, 0)
        transferThread.BeginTransfer()


if __name__ == "__main__":
    main(sys.argv)
