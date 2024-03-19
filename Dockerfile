FROM python:3.10.6

WORKDIR /app
COPY ./ ./

RUN pip install -r requirements.txt
RUN mkdir /tmp/dao

CMD python main.py
