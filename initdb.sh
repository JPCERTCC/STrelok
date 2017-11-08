#!/bin/bash

APP="strelok_app"
WEB="web"
PROJECT="compose"

if [ ! -f ./manage.py ];then
    docker-compose run --rm $WEB django-admin startproject $PROJECT .
    sudo cp $PROJECT/settings.py $PROJECT/settings.py.bk
    cat $PROJECT/settings.py.bk settings.example \
        | sed -e "s/^ROOT_URLCONF = 'compose.urls'//" \
            -e "s/db.backends.sqlite3/db.backends.postgresql/" \
            -e "s/os.path.join(BASE_DIR, 'db.sqlite3'),/'postgres','USER': 'postgres', 'HOST': 'db', 'PORT': 5432,/" \
        | sudo tee compose/settings.py
fi

if [ -d $APP/migrations ];then
	sudo rm -rfi $APP/migrations
fi
docker-compose run --rm $WEB python manage.py makemigrations $APP
docker-compose run --rm $WEB python manage.py migrate
docker-compose run --rm $WEB python manage.py loaddata $APP/fixtures/1/* $APP/fixtures/2/*
docker-compose run --rm $WEB python manage.py createsuperuser

