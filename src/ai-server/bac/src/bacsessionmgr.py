from bacsession import BacSession
from bachttpreq import BacHttpReq
import threading
import bacutil


# declare a global session manager, to make it available to 
# HTTP server RequestHandler
sessionMgr = None


class BacSessionMgr:
    # remove a session when a session is idle for MAX_IDLE_TIME seconds
    MAX_IDLE_TIME = 100
    def __init__(self, appType, localFolder, proxyMode, nextServer):
        self.appType = appType
        self.localFolder = localFolder
        self.proxyMode = proxyMode
        
        # next server is explicitly specified
        # if not, it will be specified on URL 
        self.nextServer = nextServer
        
        self.sessionCount = 0
        self.reqCount = 0           # a unique request index
        self.sessionList = list()

        self.lock = threading.Lock()

    def CreateHttpReq(self,
                      incomingReqHdlr,
                      method, 
                      path, 
                      headers):
        bacutil.DbgTrace("CreateHttpReq, from host %s, '%s %s" % 
                         (incomingReqHdlr.client_address[0], method, path))

        # Get URL
        httpReq = BacHttpReq(incomingReqHdlr)
        
        # assign a global index to each request for debugging purpose
        self.lock.acquire()
        httpReq.SetIdx(self.reqCount)
        self.reqCount += 1
        self.lock.release()
        
        httpReq.SetUrl(method, path)        
        httpReq.SetHeaders(headers)

        return httpReq
    
    # find a session that matches a new request.
    # if not found, a new session is created.
    def FindSession(self, httpReq):
        for session in self.sessionList:
            bacutil.DbgTrace("FindSession, session to host: %s, request to host %s" % 
                             (session.tgtHost, httpReq.tgtHost))
                  
            if session.MatchHttpReq(httpReq):
                return session
        
        bacutil.DbgTrace("FindSession, create a new session")
        session = BacSession(self.appType, self.localFolder)
        
        # configure a new session and start thread inside
        session.Configure(httpReq, self.sessionCount)        
        self.sessionCount = self.sessionCount + 1

        self.sessionList.append(session)

        return session

    def RemoveSession(self):
        return

    def ProcessHttpReq(self, httpReq):
        bacutil.DbgTrace("BacSessionMgr::ProcessHttpReq")
        
        session = self.FindSession(httpReq)
        
        if session is not None:
            return session.ProcessHttpReq(httpReq)

        return None