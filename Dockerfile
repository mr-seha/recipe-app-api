FROM python:3.12.10-alpine3.21
LABEL maintainer="Mohammadreza Souri"

ENV PYTHONUNBUFFERED=1
ARG DEV=false

EXPOSE 8000

RUN apk add --update --no-cache postgresql-client jpeg-dev
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev zlib zlib-dev linux-headers

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./scripts /scripts

RUN python -m venv /py
RUN /py/bin/pip install --upgrade pip

RUN /py/bin/pip install -r /tmp/requirements.txt
RUN if [ $DEV = "true" ]; \
    then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi

RUN rm -rf /tmp 
RUN apk del .tmp-build-deps

COPY ./app /app
WORKDIR /app

RUN adduser \
    --disabled-password \
    --no-create-home \
    django-user
RUN mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol/web && \
    chmod -R 755 /vol && \
    chmod +x /scripts

ENV PATH="/scripts:/py/bin:$PATH"
USER django-user

CMD ["run.sh"]