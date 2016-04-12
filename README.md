# guoku_crawler

Crawler of Guoku.


Features
--------

TODO
--------

* SqlAlchemy与数据库自动匹配,不需要手动改model.
* 有的文章中有视频，但是直接抓来的不会显示，可能需要处理一下。比如：
  [这篇文章](http://www.guoku.com/articles/4553/)。可能需要安老师协助。


How to run locally
--------

##### guoku_crawler:

    cd guoku_crawler 
    
    sudo docker-machine create --driver virtualbox [MACHINE NAME]# 如果没有machine

    sudo docker-machine ls  # 列出目前可用的machine
    
    sudo docker-machine start [MACHINE NAME] # 启动一台machine，如果上一条命令列出它的state是running，则不需要再启动
    
    docker-machine env [MACHINE NAME]
    
    eval "$(docker-machine env [MACHINE NAME])"
    
    sudo docker-compose build
    
    sudo docker-compose up  # 把worker、flower、beat全都启动 加 -d 会在后台运行
    
    sudo docker-compose run worker/flower/beat 指定启动

##### phantom-webserver:
    cd phantom-webserver
    
    sudo docker-compose build
    
    sudo docker-compose up -d
    
    sudo docker logs phantomwebserver_selenium_1 查看chrom-driver日志
    
    sudo docker logs phantomwebserver_web_1 查看phantom-webserver日志

Commonds
--------


*所有docker的命令 都需要sudo mac下除外*
*所有docker-compose命令 都要进入相对应的项目目录再执行*

#####查看docker现在在跑的东西:
    sudo docker ps
    
#####查看docker-compose正在跑的东西
    cd [PROJECT DIR]
    sudo docker-compose ps
    
#####stop a container defined in compose
    sudo docke-compose stop [CONTAINER NAME](上一条命令的结果中第一列)
    
#####stop a container otherwise
    sudo docker stop [CONTAINER ID]

#####更新后记得要先build,目前使用docker-compose
    sudo docker-compose build   需先进入相关项目的目录


#####查看日志
    sudo docker logs -f [CONTAINER ID]
    sudo docker-compose logs [CONTAINER NAME]
    eg. sudo docker-compose logs beat 查看beat的日志
        sudo docker-compose logs worker 查看worker的日志
        sudo docker-compose logs selenium 查看selenium-server的日志
        sudo docker-compose logs web  查看selenium web日志
    
#####启动guoku-crawler和phantom-webserver
    cd [PROJECT DIR]
    sudo docker-compose up -d
    
#####如何进bash
    sudo docker-compose run worker bash
    
#####如何更新guoku_crawler和phantom-webserver
    cd [PROJECT DIR]    
    sudo docker-compose stop 
    更新代码 然后重新build  
    sudo docker-compose build   
    sudo docker-compose up -d

#####如何清理image

    sudo docker ps -a   查看所有container
    sudo docker rm [[CONTAINER ID]    删除无用的container
    sudo sudo docker stop [CONTAINER ID] 停止正在跑的container
    sudo docker images 显示所有image
    sudo docker rmi [image id] 删除image
    sudo docker rmi -f [image id] 强制删除image
    
#####如何查看抓取系统是否正常运行
1. 最直接的办法是看日志，主要看guoku_crawler中worker的日志（sudo docker-compose logs worker）和phantom-webserver中的web日志（sudo docker-compose logs web）
2. 在公司连上VPN的话，可以在http://10.0.2.49:5000/_health这个链接查看phantom-webserver是否正常运行，正常的话会显示I am OK.
3. 连上VPN，在浏览器打开http://10.0.2.49:5555/dashboard，这是flower对celery任务执行的监控，在这里可以看到celery任务执行的成功与否

#####关于查看今天或者最近几小时的抓取情况
1. 可以看worker的日志，每次抓取成功都会在日志显示
2. 可以查看flower 监控celery任务,抓取文章的任务叫weixin.crawl_weixin_article, 状态未success的即为抓取成功的文章
3. 可以写SQL直接查数据库，我稍后会提供一段查询语句

    
    


    
---    
This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
