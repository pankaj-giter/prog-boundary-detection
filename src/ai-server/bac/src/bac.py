import sys
#import http.server
from bachttpserver import BacHttpServer, BacReqHandler
from baccfg import BacCfg
import bacsessionmgr
import bacutil
import ssl


def main(argv):
    bacutil.InitTrace()
    
    bacCfg = BacCfg()
    bacCfg.ParseArguments(argv)
    
    bacsessionmgr.sessionMgr = bacsessionmgr.BacSessionMgr(bacCfg.appType,
                                                           bacCfg.localFolder,
                                                           bacCfg.proxyMode,
                                                           bacCfg.nextServer)
    
    bacutil.DbgTrace("Starting server...")

    # Server settings
    server_address = ('', bacCfg.listeningPort)
    
    httpd = BacHttpServer(server_address, BacReqHandler)
    if bacCfg.listeningPort == 443 or bacCfg.listeningPort == 8443:
        httpd.socket = ssl.wrap_socket(httpd.socket, 
                                       keyfile=bacCfg.keyFile, 
                                       certfile=bacCfg.certFile, 
                                       server_side=True)
    
    bacutil.DbgTrace("Running server...")
    httpd.serve_forever()


if __name__ == '__main__':
    main(sys.argv[1:])
