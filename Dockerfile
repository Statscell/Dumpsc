FROM python:3.10-alpine

WORKDIR /

COPY . .

RUN apk add --update --no-cache --virtual .build-deps g++ zlib-dev

RUN pip install --no-cache-dir -r requirements.txt

RUN apk del .build-deps

RUN apk add --update --no-cache libstdc++

ENTRYPOINT ["python", "Main.py"]