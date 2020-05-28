FROM python:3.8.0-alpine

# set work directory
WORKDIR /usr/src/

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP db/app.py

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

RUN apk add --update gcc libc-dev linux-headers && rm -rf /var/cache/apk/*

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/requirements.txt
RUN pip install -r requirements.txt

COPY . /usr/src/
#RUN chmod +x /usr/src/docker-entrypoint.sh

#ENTRYPOINT ["/usr/src/docker-entrypoint.sh"]
COPY delete-file-cron /etc/crontabs/root

CMD flask db upgrade && python3 -m pdfbase.main
#CMD ["crond", "-f", "-d", "8"]

