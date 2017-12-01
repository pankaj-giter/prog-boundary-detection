#!/usr/bin/env python
"""
Very simple HTTP server in python.

Usage::
    ./dummy-web-server.py [<port>]

Send a GET request::
    curl http://localhost

Send a HEAD request::
    curl -I http://localhost

Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost

"""
import base64
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer

local_file_base_path = "/Users/pchaudha/dev/github/prog-boundary-detection/src/clip-webserver"
class S(BaseHTTPRequestHandler):
    def _set_headers(self, custom_headers):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        for k,v in custom_headers.items():
            self.send_header(k, v)
        self.end_headers()

    def do_OPTIONS(self):
        custom_headers = { 
                "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
                "Access-Control-Allow-Headers": "content-type",
                "Content-Type": "text/html"
                }   
        self._set_headers(custom_headers)

    def do_GET(self):
        mimetype = "application/vnd.apple.mpegurl"
        custom_headers = {
                "Content-Type": mimetype
                }
        self._set_headers(custom_headers)

        print self.path
        file_path = local_file_base_path + self.path
        print file_path

        with open(file_path, 'rb') as fp:
            self.wfile.write(fp.read())

    def do_HEAD(self):
        custom_headers = {
                "Content-Type": "text/html"
                }
        self._set_headers(custom_headers)
        
    def do_POST(self):
        custom_headers = {
                "Content-Type": "text/html"
                }
        self._set_headers(custom_headers)

        print self.path
        file_path = local_file_base_path + self.path
        print self.path

        content_length = int(self.headers["Content-Length"])

        if self.path.startswith("/cnn_image_catalog"):
            dataObj = self.rfile.read(content_length).decode("utf-8")
            dataObj = dataObj.split(";base64,")[1]
            dataObj = base64.b64decode(dataObj)

            with open(file_path, 'wb') as fp:
                fp.write(dataObj)
        else:
            with open(file_path, 'wb') as fp:
                fp.write(self.rfile.read(content_length))

        self.wfile.write("<html><body><h1>POST!</h1></body></html>")
        
def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('localhost', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
