小组项目的web后台是用Tornado写的，为了有效利用多核资源，同时达到较高的并发能力，我们在服务器开启了多个Tornado进程，并通过Nginx反向代理，实现负载均衡。另外，使用Supervisor可以方便地守护管理Tornado进程。Tornado+Supervisord+Nginx也是Tornado官方推荐的组合配置。

### 1 工具介绍

- Tornado：Web框架
- Nginx：反向代理和负载均衡
- Supervisor：管理守护进程

### 2 实验环境

- Ubuntu 14.04 LTS 64-bit
- Python 2.7.9
- Tornado 3.2.1
- Supervisor 3.1.3
- Nginx 1.8.0

### 3 环境配置

Ubuntu下，Python, Nginx通过apt-get安装，Tornado, Supervisor可通过pip安装

### 4 Tornado Web Server Demo

该Demo使用Tornado提供的options模块，可以解析命令参数。运行时加上形如```--port=8001```的命令就能按照指定端口执行，方便后面使用多进程。

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

以上Demo程序默认端口8000。运行```python demo.py -port=8080```，通过浏览器访问http://localhost:8080，页面显示“Hello 8080”。

### 5 通过Supervisor管理Tornado多进程

安装后可以使用```echo_supervisord_conf > /etc/supervisord.conf``` 生成默认配置。
Tornado官方推荐的进程数为cpu核心数。下面的配置对demo程序开了四个进程，分别运行在8001-8004端口上。

    [group:web_server]
    programs=tornado_web_demo

    [program:tornado_web_demo]
    numprocs=4
    numprocs_start=1
    command=python /home/username/www/demo.py --port=80%(process_num)02d
    process_name=%(program_name)s%(process_num)d
    directory=/home/username/www
    autorestart=true
    redirect_stderr=true
    stdout_logfile=/home/username/var/log/tornado.log
    stdout_logfile_maxbytes=500MB
    stdout_logfile_backups=50
    stderr_logfile=/home/username/var/log/tornado.log
    loglevel=info

supervisor使用命令如下：

启动supervisor：

```supervisord -c /etc/supervisord.conf```

操作托管进程：

```supervisorctl -c /etc/supervisord.conf start all```

```supervisorctl -c /etc/supervisord.conf status```

```supervisorctl -c /etc/supervisord.conf stop all```

配置更新：

```supervisorctl -c /etc/supervisord.conf update```

我们启动supervisord，使用控制台查看运行状况：

    web_server:tornado_web_demo1     RUNNING   pid 10336, uptime 0:02:18
    web_server:tornado_web_demo2     RUNNING   pid 10335, uptime 0:02:18
    web_server:tornado_web_demo3     RUNNING   pid 10334, uptime 0:02:18
    web_server:tornado_web_demo4     RUNNING   pid 10333, uptime 0:02:18

通过curl查看结果：

    $ curl http://localhost:8001
    Hello 8001
    $ curl http://localhost:8002
    Hello 8002
    $ curl http://localhost:8003
    Hello 8003
    $ curl http://localhost:8004
    Hello 8004

### 6 配置Nginx

默认配置文件位于```/etc/nginx/nginx.conf```，需要添加upstream并配反向代理，配置完成restart或reload即可。

    http {
        upstream tornadoes {
            server 127.0.0.1:8001;
            server 127.0.0.1:8002;
            server 127.0.0.1:8003;
            server 127.0.0.1:8004;
        }
        server {
            listen       8080;
            server_name  localhost;
            location / {
               proxy_set_header Host $http_host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For  $remote_addr;
               proxy_set_header X-Scheme $scheme;
               proxy_read_timeout 300s;
               proxy_pass http://tornadoes;
            }
        }
    }

常用命令：

```sudo service nginx restart```

```sudo service nginx reload```

```sudo service nginx start```

```sudo service nginx stop```
    
测试发现负载均衡效果很好：

    $ curl http://localhost:8080
    Hello 8001
    $ curl http://localhost:8080
    Hello 8002
    $ curl http://localhost:8080
    Hello 8003
    $ curl http://localhost:8080
    Hello 8004
    $ curl http://localhost:8080
    Hello 8001
    $ curl http://localhost:8080
    Hello 8002
    $ curl http://localhost:8080
    Hello 8003


### 参考：
1.[Wiki: Tornado deployment instrumentation](https://github.com/tornadoweb/tornado/wiki/Deployment#instrumentation)

2.[How To Install Nginx on Ubuntu 14.04 LTS](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-14-04-lts)

3.[Running and deploying](http://tornado.readthedocs.org/en/stable/guide/running.html)

4.[Deploy tornado application](http://blog.thisisfeifan.com/2012/06/deploy-tornado-application.html)

5.[Tornado+Supervisord+Nginx配置](http://gracece.com/2014/03/Tornado-supervisor+nginx/)

6.[生产环境优雅的重启基于Nginx、Tornado的Web服务进程](http://www.qmailer.net/archives/165.html)

7.[nginx 配置从零开始](http://oilbeater.com/nginx/2014/12/29/nginx-conf-from-zero.html)
