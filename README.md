# guoku_crawler

Crawler of Guoku.


Features
--------

* TODO

Credits
-------


Commonds
--------

#####查看docker现在在跑的东西:
    sudo docker ps
    
#####stop a container
    sudo docker stop CONTAINER ID(上一条命令的结果中第一列)

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
