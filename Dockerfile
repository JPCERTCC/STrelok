FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
RUN pip install Django psycopg2 stix2==0.2.0 dotmap requests django_datatables_view django-two-factor-auth
ADD . /code/
