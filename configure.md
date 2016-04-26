#config phantomweb server
 1. app.py 
    default_selenium_host =  phantom ip (phantom deploy ip)
    
 2. docker-compose.yml  
    for web 
    ports: 
        5000:5000
       
    for seleium
    ports:
        4444:4444
        
 

#config guoku_crawler 

  1. docker-compose.yml
    GK_PHANTOM_SERVER : deploy target ip 
  
  2. guoku_crawler.config.py 
  
    1.data_base_ip =  target database 
    2.phantom_server_ip = phantom ip 
    3.IMAGE_HOST =  'http://imgcdn.guoku.com/ for production and 48 server 
    4. IMAGE_PATH = 'images/
    5. LOCAL_FILE_STORAGE = True for production and 48 server
    6. CELERY_ALWAYS_EAGER = True 
    7. CELERYD_CONCURRENCY = 1
    8. REQUEST_INTERVAL = 2
    