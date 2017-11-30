import time
import sys


startTime = 0
logFile = 0


MSG_TRACE = 1
MSG_WARN  = 2
MSG_ERR   = 3
MSG_LOG   = 4


def InitTrace():
    global startTime
    global logFile
    
    startTime = time.time()
    logFile = open("http.log", "w")

def AppTime():
    global startTime

    # get current time
    currTime = time.time()
    
    # only keep minutes and seconds
    hours = int(currTime/3600)
    seconds = currTime - hours * 3600
    
    return seconds

def TraceFunc(msg, msgType, logFile):
    seconds = AppTime()
    
    if msgType == MSG_TRACE:
        print("[DBG - %11.6f], %s" % (seconds, msg), file = logFile)
    elif msgType == MSG_WARN:
        print("[WRN - %11.6f], %s" % (seconds, msg), file = logFile)
    elif msgType == MSG_ERR:
        print("[ERR - %11.6f], %s" % (seconds, msg), file = logFile)
    elif msgType == MSG_LOG:
        print("[LOG - %11.6f], %s" % (seconds, msg), file = logFile)

def DbgTrace(msg, msgType = MSG_TRACE):
    TraceFunc(msg, msgType, sys.stdout)

def LogTrace(msg, msgType = MSG_LOG):
    global logFile
    TraceFunc(msg, msgType, logFile)
