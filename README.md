## ParallelFileTransfer


### About
For my Networks and Distributed Systems class (CMSC 23300), we had to build a file transfer program using the protocol outlined in RFC 959. This program, written in python, is able to do that, writing the requested file in the local directory. The program is able to use either a single thread to connect to the server, or if multiple servers are provided in a batch file, then it will use one thread per line in the file to improve efficiency.

### Usage
To use the program, cd into the local directory and type in *python pftpClass.py* followed by the parameters you would like.

In order to see help, type in -h. For the version number, type in -v.

General usage is of the following format: *[-s hostname] [-f file] [options]*.

Options may include:
[-p port], [-n user], [-P password], [-l logfile]. Note that is no logfile is given, no output will be produced. If you would like to print to console, please do *'-l -'*.

An example of this is: 
*python pftpClass.py -s ftp://mirror.keystealth.org/ -f gnu/ProgramIndex*

If you wish to use a config file, the usage is *[-t config_file] [options]*. Please note that if you wish to use the config file, any options provided will be overrided by the config file information.

To produce a config file, the format is as follows:
*ftp://username:password@servername/file-path*

An example of a two thread applicaiton to download a file (though it is very likely the servers have been taken offline, this was used to grade the project):
*ftp://cs23300:youcandoit@ftp1.cs.uchicago.edu/rfc959.pdf*
*ftp://socketprogramming:rocks@ftp2.cs.uchicago.edu/rfc959.pdf*