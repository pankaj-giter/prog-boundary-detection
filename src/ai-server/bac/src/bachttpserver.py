import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from bachttpreq import BacHttpReq
import bacsessionmgr
import bacutil


_UNKNOWN = 'UNKNOWN'

# HTTPRequestHandler class
class BacReqHandler(BaseHTTPRequestHandler):
    CHUNK_DATA_NONE   = 0
    CHUNK_DATA_NORMAL = 1
    CHUNK_DATA_LAST   = 2

    # overwrite the default in BaseHTTPRequestHandler, which is "HTTP/1.0"
    protocol_version = "HTTP/1.1"
    
    #def __init__(self, request, client_address, server):
    #    BaseHTTPRequestHandler.__init__(request, client_address, server)

    def _set_headers(self, custom_headers):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        for k,v in custom_headers.items():
            self.send_header(k, v)
        self.end_headers()
  
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

    def do_OPTIONS(self):
        custom_headers = {
                "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD",
                "Access-Control-Allow-Headers": "content-type"
                }
        self._set_headers(custom_headers)

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
            # PC:
            dataObj = dataObj.decode("utf-8")
            dataObj = dataObj.split(";base64,")[1]
            dataObj = base64.b64decode(dataObj)

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

                    # PC:
                    dataObj = dataObj.decode("utf-8")
                    dataObj = dataObj.split(";base64,")[1]
                    dataObj = base64.b64decode(dataObj)

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

# multithreaded HTTP server
class BacHttpServer(ThreadingMixIn, HTTPServer):
    pass
