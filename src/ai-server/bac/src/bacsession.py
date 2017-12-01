# BacSession
#
# A session is defined as a collection of all requests to the same host.
# For each stream in MSL, the node of the next stage always has a unique host
# name. However, DNS may resolve different host names to the same IP address.
#
# A session may have multiple parallel requests in progress. each request is
# handled in a separated thread, which is started in HTTP server.


from bachttpreqbuf import BacHttpReqBuf
from bacsessionstat import BacSessionStat
from baccfg import BacCfg
from bachttpreq import BacHttpReq
from time import sleep
import http.client
import threading
import bacutil
import os
import subprocess

class BacSession:
    BO_SAMPLING_INTERVAL = 1.0
    
    SESSION_STATE_NONE    = 0
    SESSION_STATE_IDLE    = 1
    SESSION_STATE_RUNNING = 2       # streaming session is running
    SESSION_STATE_ERROR   = 3       # connection cannot be established

    SEG_STATUS_NONE         = 0
    SEG_STATUS_IN_PROGRESS  = 1
    SEG_STATUS_COMPLETED    = 2
    
    SESSION_ERR_NONE           = 0
    SESSION_ERR_INVALID_SERVER = 1
    def __init__(self, appType, localFolder):
        self.appType = appType
        self.localFolder = localFolder
        
        self.index = 0
        self.state = self.SESSION_STATE_NONE
        self.errorCode = self.SESSION_ERR_NONE
        
        # use target host as the identifier for the time being
        self.tgtHost = None
        self.segDuration = 0
        self.httpReqBuf = BacHttpReqBuf()
        self.stat = BacSessionStat()
        
        self.connection = None
        self.workThread = None
        self.monitorThread = None
        
        # HLS specific parameters
        self.currSegIdx = -1
        self.currSegState = self.SEG_STATUS_COMPLETED
    
    def Configure(self, httpReq, index):
        self.index = index
        self.state = self.SESSION_STATE_IDLE
        
        self.tgtHost = httpReq.tgtHost
        
        # start HTTP request processing thread
        # a thread is used only in aynchronous mode
        self.workThread = threading.Thread(target=self.ProcessReqBuf)
        self.workThread.start()

        # start buffer monitoring thread
        self.monitorThread = threading.Thread(target=self.MonitorBuffer)
        self.monitorThread.start()
    
    def Connect(self, tgtHost):    
        # test the dispatcher
        # tgtHost should also have port
        if self.appType == BacCfg.APP_TYPE_PROXY:
            if (tgtHost is None) or len(tgtHost) == 0:
                bacutil.DbgTrace("Connect, not a forwarding URL for PROXY. Ignored.")
            else:
                if self.connection is None:
                    try:
                        bacutil.DbgTrace("Connect, trying to connect to '%s' ..." % 
                                         tgtHost)
                        self.connection = http.client.HTTPConnection(tgtHost)
                        self.connection.connect()
                    except:
                        bacutil.DbgTrace("Connect, cannot connect to server '%s'." %
                                         tgtHost, bacutil.MSG_ERR)
                        self.connection = None
                        self.state = self.SESSION_STATE_ERROR
                        self.errorCode = self.SESSION_ERR_INVALID_SERVER
                else:
                    bacutil.DbgTrace("Connect, connection to host '%s' already exists." %
                                     self.tgtHost)
                
    def MatchHttpReq(self, httpReq):
        if self.tgtHost == httpReq.tgtHost:
            return True
        else:
            return False
    
    def PutHttpReq(self, httpReq):
        if httpReq.segDuration != 0 and self.segDuration == 0:
            bacutil.DbgTrace("Set segment target duration %d" % 
                             self.segDuration)
            self.segDuration = httpReq.segDuration
        
        # collect statistics
        self.stat.CheckReq(httpReq)
        
        self.httpReqBuf.Put(httpReq)
  
    # copied from python3. replicated here for debugging purpose
    # should call the python3 function directly
    def _readall_chunked(self, response):
        assert response.chunked != _UNKNOWN
        value = []
        try:
            while True:
                chunk_left = response._get_chunk_left()
                print("_readall_chunked, chunk_left: ", chunk_left)
                
                if chunk_left is None:
                    break
                value.append(response._safe_read(chunk_left))
                
                print("value length: ", len(value))
                
                response.chunk_left = 0
            return b''.join(value)
        except IncompleteRead:
            raise IncompleteRead(b''.join(value))

    def GenerateLocalFullPath(self, tgtPath):
        localFullPath = self.localFolder
        if (not localFullPath.endswith('/')) and (not tgtPath.startswith('/')):
            localFullPath = localFullPath + '/'
        
        localFullPath = localFullPath + tgtPath
        
        return localFullPath
    
    def ProcessGetReq(self, httpReq):
        localFullPath = self.GenerateLocalFullPath(httpReq.tgtPath)
        
        # check whether the file exists
        if not os.path.exists(localFullPath): 
            self.send_response(404)
        else:
            if httpReq.tgtPath.endswith(".txt"):
                mimetype = 'text/plain'
            elif httpReq.tgtPath.endswith(".html") or httpReq.tgtPath.endswith(".htm"):
                mimetype = 'text/html'
            elif httpReq.tgtPath.endswith(".jpg"):
                mimetype = 'image/jpg'
            elif httpReq.tgtPath.endswith(".gif"):
                mimetype = 'image/gif'
            elif httpReq.tgtPath.endswith(".js"):
                mimetype = 'application/javascript'
            elif httpReq.tgtPath.endswith(".css"):
                mimetype = 'text/css'
            elif httpReq.tgtPath.endswith(".ts"):
                mimetype = 'video/MP2T'
            elif httpReq.tgtPath.endswith(".m3u8"):
                mimetype = 'application/vnd.apple.mpegurl'
            else:
                mimetype= 'application/octet-stream'
                
            try:
                f = open(localFullPath, mode='rb')
                fileSize = os.path.getsize(localFullPath)
                
                bacutil.DbgTrace("ProcessGetReq, get file size %d." % 
                                 fileSize)
                httpReq.incomingReqHdlr.send_response(200)
                httpReq.incomingReqHdlr.send_header('Content-type', mimetype)
                httpReq.incomingReqHdlr.send_header('Content-length', fileSize)
                httpReq.incomingReqHdlr.send_header('Access-Control-Allow-Origin', '*')
                httpReq.incomingReqHdlr.end_headers()
                fileContent = f.read()                    
                f.close()

                httpReq.incomingReqHdlr.wfile.write(fileContent)
            except OSError as err:
                bacutil.DbgTrace("SendResponse, OS error: {0}".format(err))

    # make sure sub-folder exist
    def CheckPath(self, localFullPath):
        localFolder = os.path.dirname(localFullPath)
        if not os.path.exists(localFolder):
            os.makedirs(localFolder)

    # check if this is a playlist file
    def ProcessCompletedFile(self, filePath):
        # tech-jam code
        resultPath = None
        if "tech-jam" in filePath:
            # copy file to S3
            print("Copy %s to S3" % filePath)
            subprocess.call(['aws', 's3', 'cp', filePath, 's3://pw_public/video.jpg'])
            
            # run aws rekognition API
            # aws rekognition detect-text --image '{"S3Object":{"Bucket":"pw_public","Name":"video.jpg"}}' --region us-east-1
            resultPath = self.GenerateLocalFullPath("rek.txt")
            resultFile = open(resultPath, "w")
            subprocess.call(['aws', 'rekognition', 'detect-text', '--image', '{"S3Object":{"Bucket":"pw_public","Name":"video.jpg"}}', '--region', 'us-east-1'], stdout=resultFile)

        # 1. if it is master playlist
        
        # 2. if it is bitrate playlist
        
        # 3. it is segment
        return resultPath

    # find whether the image 
    #def DetectBreakingNews(self, ):

    def ProcessPutReq(self, httpReq):
        localFullPath = self.GenerateLocalFullPath(httpReq.tgtPath)

        bacutil.DbgTrace("Post object of length %d" % len(httpReq.dataObj))
        
        if (httpReq.dataObj is not None) and len(httpReq.dataObj) > 0:
            if httpReq.postedFile is None:
                self.CheckPath(localFullPath)
                httpReq.postedFile = open(localFullPath, mode='wb')
                
            httpReq.postedFile.write(httpReq.dataObj)
        
        # finish the writing of the file, and send response
        if (httpReq.postedFile is not None):
            if (not httpReq.chunkedEncoding) or httpReq.lastChunk:
                httpReq.postedFile.close()
                
                resultPath = self.ProcessCompletedFile(localFullPath)
                
                httpReq.postedFile = None
                
                # send response
                fileSize = 0
                fileContent = None
                if resultPath is not None:
                    f = open(resultPath, mode='r')
                    fileSize = os.path.getsize(resultPath)
                    fileContent = f.read()                    
                    f.close()
                
                httpReq.incomingReqHdlr.send_response(200)
                httpReq.incomingReqHdlr.send_header('Access-Control-Allow-Origin', '*')

                # PC:
                httpReq.incomingReqHdlr.send_header('Content-length', 0)

                #if fileSize > 0:
                #    httpReq.incomingReqHdlr.send_header('Content-type', 'text/plain')
                #    httpReq.incomingReqHdlr.send_header('Content-length', fileSize)

                if fileContent is not None:
                    returnStatus = "None"
                    print(type(fileContent))
                    
                    """
                    if "CN" in fileContent:
                        returnStatus = "CNN"
                        if "BREAKING" in fileContent:
                            returnStatus = "CNN-Breaking news"
                    """
                    # PC: more fine tuning of the AI image recognition logic
                    to_search = ["CN", "CNN", "BREAKING NEWS", "COMING UP", "ONLY ON", "DEVELOPING"]
                    for s in to_search:
                        if s in fileContent:
                            returnStatus = "CNN"
                        
                    httpReq.incomingReqHdlr.send_header('Access-Control-Expose-Headers', 'Akamai-Program-Detection')
                    httpReq.incomingReqHdlr.send_header('Akamai-Program-Detection', returnStatus)
                    bacutil.DbgTrace('Akamai-Program-Detection %s' % returnStatus)
                    
                httpReq.incomingReqHdlr.end_headers()

#                if fileSize > 0:
#                    httpReq.incomingReqHdlr.wfile.write(fileContent)
        
    def ProcessLocalReq(self, httpReq):
        # local host
        bacutil.DbgTrace("ProcessLocalReq, local command '%s %s'" % 
                         (httpReq.method, httpReq.tgtPath))

        if httpReq.method == BacHttpReq.HTTP_METHOD_GET:
            self.ProcessGetReq(httpReq)
            httpReq.Log()
        elif (httpReq.method == BacHttpReq.HTTP_METHOD_PUT) or \
            (httpReq.method == BacHttpReq.HTTP_METHOD_POST):
            self.ProcessPutReq(httpReq) 
            httpReq.Log()

    def ForwardHttpReq(self, httpReq):
        response = None
        self.Connect(httpReq.tgtHost)
        
        if self.connection is None:
            bacutil.DbgTrace("ForwardHttpReq, Req not processed: '%s http://%s/%s'" % 
                             (httpReq.method, httpReq.tgtHost, httpReq.tgtPath),
                             bacutil.MSG_ERR)
            return None
        
        if httpReq.segDuration != 0 and self.segDuration == 0:
            bacutil.DbgTrace("ForwardHttpReq, set segment target duration %d" % 
                             self.segDuration)
            self.segDuration = httpReq.segDuration
        
        # send request headers
        if (not httpReq.chunkedEncoding) or (httpReq.chunkIdx == 0):
            bacutil.DbgTrace("ForwardHttpReq, request '%s http://%s%s'" %
                             (httpReq.method, httpReq.tgtHost, httpReq.tgtPath))
            self.connection.putrequest(httpReq.method, httpReq.tgtPath)
            
            # send all the keys in the incoming headers, except 'Host'
            keys = httpReq.headers.keys()
            for key in keys:
                # get the value for each key
                if key == 'Host':
                    # replace 'Host' with the host of the next hop
                    self.connection.putheader('Host', httpReq.tgtHost)
                else:
                    self.connection.putheader(key, httpReq.headers.get(key))
            
            self.connection.endheaders()

        # send data
        if httpReq.dataObj:
            bacutil.DbgTrace("ForwardHttpReq, %d bytes" % 
                             (len(httpReq.dataObj)))
            if httpReq.chunkedEncoding:
                bacutil.DbgTrace("ForwardHttpReq, chunk %d" % 
                                 httpReq.chunkIdx)

                numStr = "%x\r\n" % len(httpReq.dataObj)                
                sendData = bytes(numStr, "utf-8")
                # try to call connection.send only once
                if len(httpReq.dataObj) > 0:
                    # "utf-8" encoding should not change the bytes in string
                    sendData = bytes(numStr, "utf-8") + httpReq.dataObj + b'\r\n'

                self.connection.send(sendData)
            else:
                self.connection.send(httpReq.dataObj)
        
        # a response is expected only if not chunk encoding, or the end of chunk
        if (not httpReq.chunkedEncoding) or (httpReq.lastChunk):
            response = self.connection.getresponse()
            
        bacutil.DbgTrace("ForwardHttpReq, exit")
        
        return response
  
    def SendResponse(self, httpReq, forwardedRsp):
        # headers is from http.client.HTTPConnection.getresponse().getheaders()
        # headers is a list of (key, value) pair
        httpReq.incomingReqHdlr.send_response(200)
        for field in forwardedRsp.getheaders():
            httpReq.incomingReqHdlr.send_header(field[0], field[1])
        
        httpReq.incomingReqHdlr.end_headers()
        
        contentLength = forwardedRsp.getheader('Content-Length')
        if contentLength is None:
            bacutil.DbgTrace("Forward chunked response ...")
            encoding = forwardedRsp.getheader('Transfer-Encoding')
            if encoding == 'chunked':
                # pass the chunks to the client
                status = self.CHUNK_DATA_NONE
                while True:
                    chunkSize = forwardedRsp._get_chunk_left()
                    #chunkData = forwardedRsp.read1(chunkSize)
                    chunkData = self._readall_chunked(forwardedRsp)
                    bacutil.DbgTrace("chunk size: %d, chunkData length: %d" % 
                                     (chunkSize, len(chunkData)))
                    bacutil.DbgTrace("chunkData: type %s\n%s" % 
                                     (type(chunkData), chunkData))
                    
                    if chunkData == '':
                        status = self.CHUNK_DATA_LAST

                    if status != self.CHUNK_DATA_LAST:
                        numStr = "%x\r\n" % len(chunkData)
                        
                        # "utf-8" encoding should not change the bytes in string
                        httpReq.incomingReqHdlr.wfile.write(bytes(numStr, "utf-8"))
                        httpReq.incomingReqHdlr.wfile.write(bytes(chunkData))
                        httpReq.incomingReqHdlr.wfile.write(b'\r\n')
                        
                    if chunkSize == len(chunkData):
                        status = self.CHUNK_DATA_LAST
                        break

                httpReq.incomingReqHdlr.wfile.write(b'0\r\n\r\n')
        else:
            rspMsg = forwardedRsp.read(int(contentLength))

            bacutil.DbgTrace("Content-Length: %s" % contentLength)
            bacutil.DbgTrace("rspMsg of type %s:\n" % type(rspMsg), rspMsg)
            httpReq.incomingReqHdlr.wfile.write(rspMsg)

    def ProcessHttpReq(self, httpReq):
        # proxy request
        bacutil.DbgTrace("ProcessHttpReq, method %s, chunkedEncoding %r" %
                         (httpReq.method, httpReq.chunkedEncoding))

        response = None
        if httpReq.tgtHost == '':
            self.ProcessLocalReq(httpReq)
        else:
            response = self.ForwardHttpReq(httpReq)
            self.SendResponse(httpReq, response)
            
        return response

    def ProcessReqBuf(self):
        bacutil.DbgTrace("Session::ProcessHttpReq")
        while True:
            httpReq = self.httpReqBuf.Get()
            if httpReq is None:
                bacutil.DbgTrace("Session::ProcessHttpReq httpReq invalid.")
                continue
            
            self.ProcessHttpReq(httpReq)

    def MonitorBuffer(self):
        bacutil.DbgTrace("Session::MonitorBuffer")
        while True:
            # check buffer
            pendingReqs = self.httpReqBuf.NumPendingReqs()
            mediaObjs = self.httpReqBuf.NumMediaObjs()
            mediaDataBytes = self.httpReqBuf.NumMediaBytes()
            mediaBufferedTime  = mediaObjs * self.segDuration
            
            if pendingReqs > 0:
                bacutil.DbgTrace("Buffered requests %2d, media objects %2d, data: %5d Kbytes, %5.1f Seconds." % 
                                 (pendingReqs, mediaObjs, mediaDataBytes, mediaBufferedTime))
            
            sleep(self.BO_SAMPLING_INTERVAL)
            
