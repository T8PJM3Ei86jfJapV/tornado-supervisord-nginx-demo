#-*-coding:utf-8-*-

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello " + str(options.port))

settings = {  
    "debug": True,  
}

application = tornado.web.Application([  
    (r"/", MainHandler),  
], **settings)  

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)  
    tornado.options.parse_command_line()  
    http_server.listen(options.port)  
    tornado.ioloop.IOLoop.instance().start()