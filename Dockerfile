FROM python:3.7.3-alpine3.9

ADD src /app

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["-m", "swagger_server"]
