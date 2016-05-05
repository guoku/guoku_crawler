docker-compose stop
docker ps -a | grep guokucrawler | awk '{print $1}' | xargs docker rm
docker rmi guokucrawler_beat
docker rmi guokucrawler_flower
docker rmi guokucrawler_cookie_worker
docker rmi guokucrawler_worker
docker-compose build