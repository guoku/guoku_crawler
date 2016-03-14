#!/usr/bin/env bash
set -e
case $1 in
    worker)
    exec celery -A guoku_crawler worker -l info
    ;;

    beat)
	exec celery -A guoku_crawler beat -l info
    ;;

    flower)
    exec flower -A guoku_crawler --auto_refresh=True --address=0.0.0.0 --port=5000 --basic-auth=guoku:guoku1@#
    ;;

    *)
    exec "$@"
    ;;
esac
