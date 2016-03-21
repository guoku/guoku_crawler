# guoku_crawler

Crawler of Guoku.


Features
--------

TODO
--------

* SqlAlchemy与数据库自动匹配,不需要手动改model.


How to run locally
--------
    cd guoku_crawler 
    
    sudo docker-machine create --driver virtualbox [MACHINE NAME]# 如果没有machine

    sudo docker-machine ls  # 列出目前可用的machine
    
    sudo docker-machine start [MACHINE NAME] # 启动一台machine，如果上一条命令列出它的state是running，则不需要再启动
    
    docker-machine env [MACHINE NAME]
    
    eval "$(docker-machine env [MACHINE NAME])"
    
    sudo docker-compose build
    
    sudo docker-compose up  # 把worker、flower、beat全都启动
    
    sudo docker-compose run worker/flower/beat 指定启动


Commonds
--------
*所有docker的命令 都需要sudo*

#####查看docker现在在跑的东西:
    sudo docker ps
    
#####查看docker-compose正在跑的东西
    sudo docker-compose ps
    
#####stop a container defined in compose
    sudo docke-compose stop CONTAINER ID(上一条命令的结果中第一列)
    
#####stop a container otherwise
    sudo docker stop CONTAINER ID

#####更新后记得要先build
    sudo docker build -t phantom-webserver .
    guoku_crawler同理

#####查看日志
    sudo docker logs -f CONTAINER ID

#####启动chrome-driver

    sudo docker run --privileged -p 10.0.2.49:4444:4444 --rm selenium/standalone-chrome -d
    
#####启动phantom-webserver
    sudo docker run -p 10.0.2.49:5000:5000 -d phantom-webserver
    
#####启动guoku-crawler
    sudo docker-compose up -d
    
#####如何进bash
    sudo docker-compose run worker bash
    
    
---    
This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
