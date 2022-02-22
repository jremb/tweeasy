FROM python:3.10.2-alpine3.15

WORKDIR /code

COPY ./requirements.txt /requirements.txt 

RUN pip install --no-cache-dir --upgrade -r /requirements.txt

COPY ./src/ /code/src/

CMD ["python3", "/code/src/main.py"]