from bachttpreq import BacHttpReq

class BacSessionStat:
    def __init__(self):
        self.numGetReqs = 0
        self.numPutReqs = 0
        self.numPostReqs = 0
        self.numDeleteReqs = 0
        self.numOtherReqs = 0
        
        self.putBytes = 0
        self.postBytes = 0

    def CheckReq(self, httpReq):
        if httpReq.method == BacHttpReq.HTTP_METHOD_GET:
            self.numGetReqs = self.numGetReqs + 1
        elif httpReq.method == BacHttpReq.HTTP_METHOD_PUT:
            self.numPutReqs = self.numPutReqs + 1
            self.putBytes = self.putBytes + len(httpReq.dataObj)
        elif httpReq.method == BacHttpReq.HTTP_METHOD_POST:
            self.numPostReqs = self.numPostReqs + 1
            self.postBytes = self.postBytes + len(httpReq.dataObj)
        elif httpReq.method == BacHttpReq.HTTP_METHOD_DELETE:
            self.numDeletReqs = self.numDeletReqs + 1
        else:
            self.numOtherReqs = self.numOtherReqs + 1

    def Trace(self):
        print("Total reqests: ％, GET %d, PUT %d, POST %d, DELETE %d" %
              self.numGetReqs + 
              self.numPutReqs + 
              self.numPostReqs + 
              self.numDeleteReqs + 
              self.numOtherReqs)
        if self.numPutReqs > 0 or self.numPostReqs > 0:
            print("    Data bytes received: PUT %d, POST %d" %
                  (self.putBytes, self.postBytes))
        