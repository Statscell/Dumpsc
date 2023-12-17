FROM python:3.10-alpine

WORKDIR /app

COPY . .

RUN apk add --update --virtual .build-deps \
        g++ \
        jpeg-dev \
        python3-dev \
        zlib-dev

RUN pip install --no-cache-dir setuptools wheel

RUN pip install --no-cache-dir -r requirements.txt

RUN apk del .build-deps

RUN apk add --update --no-cache \
        jpeg \
        libstdc++

ENTRYPOINT ["python", "Main.py"]