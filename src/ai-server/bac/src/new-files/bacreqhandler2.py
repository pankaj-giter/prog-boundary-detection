from bachttpreq import BacHttpReq
import bacsessionmgr
import bacutil


_UNKNOWN = 'UNKNOWN'

# HTTPRequestHandler class
class BacReqHandler2(Thread):
    CHUNK_DATA_NONE   = 0
    CHUNK_DATA_NORMAL = 1
    CHUNK_DATA_LAST   = 2
    
    def __init__(self):
        # client connection
        self.socket = None
        self.code = 200
        self.respHdrStr = ""

    # following functions are defined similar to those in http.server
    # send_response must be called first
    def send_response(self, code):
        self.code = code
        self.respHdrStr = ""
    
    # send_header is called for each field
    def send_header(self, keyword, value):
        self.respHdrStr = self.respHdrStr + keyword + ": " + value + "\r\n"

    # terminate headers
    def end_headers(self):
        self.respHdrStr = self.respHdrStr + "\r\n"

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
  
    def SendRespMsg(self):
        if self.socket is None:
            bacutil.DbgTrace("handler does not have valid socket open for the .", type)
            return 0
        
        self.socket.sendall(self.respHdrStr)
  
    # GET handler
    def do_GET(self):
        httpReq = bacsessionmgr.sessionMgr.CreateHttpReq(self, 
                                                         BacHttpReq.HTTP_METHOD_GET,
                                                         self.path,
                                                         self.headers)
        bacsessionmgr.sessionMgr.ProcessHttpReq(httpReq)

    # GET handler
    def do_DELETE(self):
        httpReq = bacsessionmgr.sessionMgr.CreateHttpReq(self,
                                                         BacHttpReq.HTTP_METHOD_DELETE,
                                                         self.path,
                                                         self.headers)
        bacsessionmgr.sessionMgr.ProcessHttpReq(httpReq)

    # POST handler
    def do_POST(self):
        self.PostPutCommon(BacHttpReq.HTTP_METHOD_POST)

    # POST handler
    def do_PUT(self):
        self.PostPutCommon(BacHttpReq.HTTP_METHOD_PUT)

    def PostPutCommon(self, method):
        bacutil.DbgTrace("PostPutCommon enter ...")
        
        # Get file
        if self.headers['Content-Length'] is not None:
            length = int(self.headers['Content-Length'])
            
            bacutil.DbgTrace("PostPutCommon, Content-length: %d." % 
                             length)
            
            #dataObj = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
            #for key, value in dataObj.items():
            #    print("%s: %s" % (key, value))
            dataObj = self.rfile.read(length)#.decode('utf-8')
            httpReq = bacsessionmgr.sessionMgr.CreateHttpReq(self,
                                                             method,
                                                             self.path,
                                                             self.headers)
            httpReq.SetDataObj(dataObj)
            bacsessionmgr.sessionMgr.ProcessHttpReq(httpReq)
        else:
            bacutil.DbgTrace("PostPutCommon, chunked.")
            
            if self.headers['Transfer-Encoding'] == "chunked":
                httpReq = None
                status = self.CHUNK_DATA_NONE
                while status != self.CHUNK_DATA_LAST:
                    status, dataObj = self.GetReqChunkedData(self.rfile)
                    if httpReq is None:
                        httpReq = bacsessionmgr.sessionMgr.CreateHttpReq(self,
                                                                         method,
                                                                         self.path,
                                                                         self.headers)

                    httpReq.SetDataObj(dataObj)
                    #print("@@@@ dataObj:\n", dataObj)
                    bacsessionmgr.sessionMgr.ProcessHttpReq(httpReq)
            else:
                bacutil.DbgTrace("REQ Content-Length not found, and not chunked.")
                self._set_headers()
                message = "Return from POST!\n"
                self.wfile.write(bytes(message, "utf8"))
                
        bacutil.DbgTrace("PostPutCommon leave ...")

    # inputStream: io.BufferedIOBase
    def GetReqChunkedData(self, inputStream):
        # read the size field, also remove "\r\n" from input stream
        # inputStream.read returns "bytes" object
        sizeStr = inputStream.read(2)
        while sizeStr[-2:] != b"\r\n":
            sizeStr += inputStream.read(1)
        
        chunkSize = int(sizeStr[:-2], 16)
        bacutil.DbgTrace("GetReqChunkedData, chunk size %d." %  chunkSize)
        
        status = self.CHUNK_DATA_NONE
        if chunkSize == 0:
            # return an empty object
            dataObj = bytes()
            status = self.CHUNK_DATA_LAST
        else:
            dataObj = inputStream.read(chunkSize)
            status = self.CHUNK_DATA_NORMAL
        
        # remove "\r\n", which is in addition to data, from input stream
        inputStream.read(2)
        
        return status, dataObj

    def run(self):
        