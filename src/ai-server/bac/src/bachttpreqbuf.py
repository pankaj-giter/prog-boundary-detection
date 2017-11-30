# HttpReqBuf
#
# Buffer to hold all unprocessed requests. 
# It is used in storing all unclassified requests, and each session to store 
# the pending requests of a session.


import threading
from bachttpreq import BacHttpReq


class BacHttpReqBuf:
    MAX_PENDING_REQ = 1000
    def __init__(self):
        self.reqList = list()
        self.semaphore = threading.Semaphore(value=0)

        self.lock = threading.Lock()
        
    def Put(self, httpReq):
        if httpReq is None:
            print("Invalid request object.")
        
        # lock is still required since there can be multiple pending requests
        self.lock.acquire()
        self.reqList.append(httpReq)
        self.lock.release()

        self.semaphore.release()
        
    def Get(self):
        self.semaphore.acquire()
        
        if len(self.reqList) == 0:
            print("Should not happen since semaphore is acquired.")
            return None
        
        self.lock.acquire()
        seg = self.reqList.pop(0)
        self.lock.release()
        
        return seg

    def NumPendingReqs(self):
        return len(self.reqList)

    # Media object is non-manifest objects
    def NumMediaObjs(self):
        numObjs = 0
        self.lock.acquire()
        for httpReq in self.reqList:
            if httpReq.reqType == BacHttpReq.REQ_SEGMENT:
                numObjs = numObjs + 1
        self.lock.release()
        return numObjs
    
    def NumMediaBytes(self):
        numBytes = 0
        self.lock.acquire()
        for httpReq in self.reqList:
            numBytes = numBytes + httpReq.NumBytes()
        self.lock.release()
        
        return numBytes
