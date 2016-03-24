# guoku_crawler

Crawler of Guoku.


Features
--------

TODO
--------

* SqlAlchemy与数据库自动匹配,不需要手动改model.


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

#####查看docker现在在跑的东西:
    sudo docker ps
    
#####查看docker-compose正在跑的东西
    cd [PROJECT DIR]
    sudo docker-compose ps
    
#####stop a container defined in compose
    sudo docke-compose stop [CONTAINER NAME](上一条命令的结果中第一列)
    
#####stop a container otherwise
    sudo docker stop [CONTAINER ID]

#####更新后记得要先build
    sudo docker build -t phantom-webserver .
    guoku_crawler同理

#####查看日志
    sudo docker logs -f [CONTAINER ID]
    sudo docker-compose logs [CONTAINER NAME]
    
#####启动guoku-crawler和phantom-webserver
    cd [PROJECT DIR]
    sudo docker-compose up -d
    
#####如何进bash
    sudo docker-compose run worker bash
    
#####如何更新guoku_crawler和phantom-webserver
    cd [PROJECT DIR]    
    sudo docker-compose stop   
    sudo docker-compose build   
    sudo docker-compose up -d
    
    
---    
This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
