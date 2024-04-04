#!/usr/bin/env python3

"""
parse audit events and sends them to syslog after changing uid to username
"""


"""
Todo
1. Check if we have the correct permission to run the audit.
2. syslog.closelog when terminated.
"""

__author__ = ""                                                                                                                                 
__credits__ = [""]                                                                                                                              
__license__ = "GPL"                                                                                                                                            
__version__ = "1.0"
__maintainer__ = ""
__email__ = ""
__status__ = ""

import os
import signal
import sys
from circularBuffer import StringCircularBuffer
from util import Util
from auParser import AuParser
from threading import Thread

stop = 0
hup = 0

def termHandler(sig, msg):
    global stop 
    print("received a %d event, message: %d", sig, msg)
    stop = 1
    sys.exit(0)

def hupHandler(sig, msg):
    global hup
    print("received a %d event, message: %s", sig, msg)
    hup = 1

def reloadConfig():
    global hup
    hup = 0

signal.signal(signal.SIGHUP, hupHandler)
signal.signal(signal.SIGTERM, termHandler)

#buf=sys.stdin.readlines()
programname = os.path.basename(sys.argv[0])
        
def auditDispatcherThread(rbAuditEvent):
    global stop
    global hup
    auparser = AuParser(rbAuditEvent)

    while stop == 0:
        try:
            #buf=sys.stdin.readlines()
            #buf=sys.stdin
            f = open("test.log", "r")
            if hup == 1 :
                reloadConfig()
                continue
            for line in f.readlines():
                auparser.auditParse(line)
            #print(str(rb))
        except IOError as e:
            print("IOError: %s" % (e))
            continue
        except ValueError as e:
            print("ValueError %s" % (e))
        stop = 1

def auditLoggerThread(filename, rbAuditEvent):
    global stop
    global hup

    util = Util(filename)

    # ringBuffer for 512 Security Events
    rbLogger = StringCircularBuffer(512)
    while True:
        try:
            if not rbAuditEvent.is_empty() and not rbLogger.is_full():
                rbLogger.enqueue(rbAuditEvent.dequeue())

            if rbLogger.is_full():
                util.encryptLogFile(rbLogger.flush_content())
                continue
            #get the last piece of data out from the ring buffer.
            elif not rbAuditEvent.is_empty():
                continue
            elif stop:
                util.encryptLogFile(rbLogger.flush_content())
                break
        except Exception as e:
            print("unable to enqueue/dequeue to ringbuffer: %s" % (e))
            break

def main():
    rbAuditEvent = StringCircularBuffer(8196)
    filename = "demofile"

    threads = []
    t1 = Thread(target=auditDispatcherThread, args=(rbAuditEvent,))
    t2 = Thread(target=auditLoggerThread, args=(filename, rbAuditEvent,))
    t1.start()
    t2.start()
    threads.append(t1)
    threads.append(t2)
    
    while stop == 0:
          if stop == 1:
                break
    
    t1.join()
    t2.join()

if  __name__ =='__main__':
        main()
