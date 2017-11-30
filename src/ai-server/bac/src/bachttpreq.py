from urllib.parse import urlparse
import bacutil
import socket


globalHttpReqIdx = 0


class BacHttpReq:
    REQ_NONE             = 0
    REQ_MASTER_MANIFEST  = 1
    REQ_BITRATE_MANIFEST = 2
    REQ_SEGMENT          = 3
    
    HTTP_METHOD_NONE   = 'NONE'
    HTTP_METHOD_GET    = 'GET'
    HTTP_METHOD_PUT    = 'PUT'
    HTTP_METHOD_POST   = 'POST'
    HTTP_METHOD_DELETE = 'DELETE'
    
    def __init__(self, incomingReqHdlr):
        global globalHttpReqIdx
        # a unique ID, tracked for debug purpose
        self.globalHttpReqIdx = globalHttpReqIdx
        globalHttpReqIdx += 1
        
        self.idx = 0
        self.reqType = self.REQ_NONE
        
        self.reqTimeStart = bacutil.AppTime()
        self.reqTimeEnd   = 0
        
        self.incomingReqHdlr = incomingReqHdlr
        self.method = self.HTTP_METHOD_NONE
        self.headers = None
        self.tgtUrl = None
        self.tgtHost = None
        self.tgtPath = None
        self.segDuration = 0            # target segment duration from playlist
        self.dataObj = None
        
        # parameters for chunked encoding
        self.postedFile = None          # used in both post and put
        self.chunkedEncoding = False
        self.chunkIdx = 0
        self.lastChunk = False
    
    def SetIdx(self, idx):
        self.idx = idx
    
    # check whether tgtHost is a valid host name
    def CheckTgtHost(self, tgtHost):
        validHost = False
        
        hostPortList = tgtHost.split(":")
        sHost = hostPortList[0]
        
        # check port
        
        # check host
        try:
            tokens = sHost.split('.')
            if len(tokens) == 4:
                socket.inet_aton(sHost)
                validHost = True
        except socket.error:
            tokenList = sHost.split(".")
            if len(tokenList) == 1:
                if sHost == 'localhost':
                    validHost = True
            elif tokenList[-1] == 'com' or tokenList[-1] == 'net':
                validHost = True
        
        return validHost
    
    def SetUrl(self, method, url):
        # parse URL
        # URL is formed as "http://proxyIP:port/targetUrl"
        # 1. Extract the target URL
        self.method = method
        
        parsedTgtUrl = urlparse('http:/' + url)
        validHost = self.CheckTgtHost(parsedTgtUrl.netloc)
        
        if validHost:
            self.tgtUrl = 'http:/' + url
            self.tgtHost = parsedTgtUrl.netloc
            self.tgtPath = parsedTgtUrl.path
        else:
            # a local file
            self.tgtUrl = url
            self.tgtHost = ''
            self.tgtPath = self.tgtUrl
            
        bacutil.DbgTrace("SetUrl, host '%s', path '%s'" % 
                         (self.tgtHost, self.tgtPath))
            
    def SetHeaders(self, headers):
        self.headers = headers
        if self.headers['Transfer-Encoding'] == "chunked":
            self.chunkedEncoding = True
            self.chunkIdx = -1
            self.lastChunk = False
            
        bacutil.DbgTrace("SetHeaders, chunkedEncoding %r" % 
                         self.chunkedEncoding)
        
    def SetDataObj(self, dataObj):
        # check input variable
        if dataObj is None:
            self.dataObj = None
            bacutil.DbgTrace("SetDataObj, Data object is invalid.")
            return False

        if self.tgtUrl is None:
            bacutil.DbgTrace("SetDataObj, URL not configured.")
            return False
        
        self.dataObj = dataObj
        if self.chunkedEncoding:
            self.chunkIdx += 1

        bacutil.DbgTrace("SetDataObj, req %d, size %d, chunked %r, chunkIdx %d" % 
                         (self.globalHttpReqIdx, 
                          len(dataObj), 
                          self.chunkedEncoding, 
                          self.chunkIdx))
        
        if len(dataObj) == 0:
            if self.chunkedEncoding:
                self.lastChunk = True
            return True

        if (not self.chunkedEncoding) or (self.chunkIdx == 0):
            # check object type by looking at the first several bytes
            self.reqType = self.REQ_NONE
            
            if self.tgtPath.endswith('.m3u8'):
                if dataObj[0 : 7] != b'#EXTM3U':
                    bacutil.DbgTrace("SetDataObj, invalid m3u8 file format.")
                else:
                    # convert to a string object
                    playlistStr = dataObj.decode("utf-8")
                    
                    # check whether this is master (variant) playlist
                    if "EXT-X-STREAM-INF" in playlistStr:
                        bacutil.DbgTrace("SetDataObj, master playlist")
                        self.reqType = self.REQ_MASTER_MANIFEST
                    else:
                        bacutil.DbgTrace("SetDataObj, bitrate playlist")
                        self.reqType = self.REQ_BITRATE_MANIFEST
                    
                    playlistStrLines = playlistStr.split('\n')
                    for line in playlistStrLines:
                        if "EXT-X-TARGETDURATION" in playlistStr:
                            # extract target segment duration from playlist
                            tokens = line.split(':')
                            if len(tokens) == 2:
                                self.segDuration = int(tokens[1])
                            else:
                                bacutil.DbgTrace("SetDataObj, invalid EXT-X-TARGETDURATION line in playlist file.")
                            break
            elif self.tgtPath.endswith('.ts'):
                # do not know yet. will check if it belongs to any session
                bacutil.DbgTrace("SetDataObj, segment")
                self.reqType = self.REQ_SEGMENT
            else:
                bacutil.DbgTrace("SetDataObj, '%s' file type not recognized." %
                                 self.tgtPath)
        
    def NumBytes(self):
        if self.dataObj is None:
            return None
        else:
            return self.dataObj.size()

    def Log(self):
        self.reqTimeEnd = bacutil.AppTime()
        bacutil.LogTrace("[%12.6f ~ %12.6f] %s %s" %
                         (self.reqTimeStart, self.reqTimeEnd, self.method, self.tgtUrl))
        