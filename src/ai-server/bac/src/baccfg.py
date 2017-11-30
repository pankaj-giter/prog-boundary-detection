import argparse


class BacCfg:
    PROXY_MODE_SYNC  = 1
    PROXY_MODE_ASYNC = 2
    
    APP_TYPE_SERVER  = 1
    APP_TYPE_PROXY   = 2
    
    DEFAULT_PORT     = 8800
    DEFAULT_FOLDER   = "www"      # where server is started
    DEFAULT_CERT     = "cert/cert.pem"
    DEFAULT_KEY     = "cert/key.pem"
    
    def __init__(self):
        self.appType = self.APP_TYPE_PROXY
        self.localFolder = self.DEFAULT_FOLDER        
        self.listeningPort = self.DEFAULT_PORT        
        self.proxyMode = self.PROXY_MODE_SYNC
        self.nextServer = None
        self.certFile = None
        self.keyFile = None
        
    def ParseArguments(self, argv):
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--port', action='store', dest='listeningPort',
                            default=self.DEFAULT_PORT, type=int,
                            help="listening port: port that proxy/server is listening to.")
        parser.add_argument('--folder', action='store', dest='localFolder',
                            default=self.DEFAULT_FOLDER, type=str,
                            help="local file folder.")
        parser.add_argument('--cert', action='store', dest='certFile',
                            default=self.DEFAULT_CERT, type=str,
                            help="certificate file.")
        parser.add_argument('--key', action='store', dest='keyFile',
                            default=self.DEFAULT_KEY, type=str,
                            help="key file.")
        parser.add_argument('--type', action='store', dest='appType',
                            default='proxy', type=str,
                            help="proxy, forward data, server: only receive data.")
        parser.add_argument('--next', action='store', dest='nextServer',
                            default='0.0.0.0', type=str,
                            help="'IPAddr:port': of server to forward data. Used only for proxy.")
        parser.add_argument('--mode', action='store', dest='proxyMode',
                            default='sync', type=str,
                            help="sync: synchronous, async: asynchronous (ACK POST/PUT immediately, other methods are still synchronous).")

        args = parser.parse_args(argv)
        
        self.listeningPort = args.listeningPort
        if args.appType == "proxy":
            self.appType = self.APP_TYPE_PROXY
        else:
            self.appType = self.APP_TYPE_SERVER

        self.localFolder = args.localFolder
        
        self.certFile = args.certFile
        self.keyFile = args.keyFile
        
        if args.nextServer != '0.0.0.0':
            # should perform checking
            self.nextServer = args.nextServer

        if args.proxyMode == "sync":
            self.proxyMode = self.PROXY_MODE_SYNC
        elif args.proxyMode == "async":
            self.proxyMode = self.PROXY_MODE_ASYNC
        else:
            print("Invalid proxy mode %s, default to synchronous." % args.proxyMode)
            self.proxyMode = self.PROXY_MODE_SYNC
