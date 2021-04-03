FROM python:3.9.2-alpine3.13

WORKDIR /app/

EXPOSE 5000

ENV GROUP_ID=1000 \
    USER_ID=1000

ADD ./app/requirements.txt ./
RUN pip install -r requirements.txt
ADD ./app/ .

RUN addgroup -g $GROUP_ID www
RUN adduser -D -u $USER_ID -G www www -s /bin/sh

USER www

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]