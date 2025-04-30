FROM python:3.12.10-alpine3.21
LABEL maintainer="Mohammadreza Souri"

ENV PYTHONUNBUFFERED=1
ARG DEV=true

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app

EXPOSE 8000

RUN python -m venv /py
RUN /py/bin/pip install --upgrade pip

RUN apk add --update --no-cache postgresql-client
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev

RUN /py/bin/pip install -r /tmp/requirements.txt
RUN if [ $DEV = "true" ]; \
    then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi
 
RUN rm -rf /tmp 
RUN apk del .tmp-build-deps 

RUN adduser \
    --disabled-password \
    --no-create-home \
    django-user

ENV PATH="/py/bin:$PATH"
USER django-user