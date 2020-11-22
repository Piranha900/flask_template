FROM python:3.8-slim
ADD requirements.txt /
RUN pip3 install --upgrade -r /requirements.txt
ADD . /app
ENV PYTHONPATH=$PYTHONPATH:/app/
WORKDIR /app

EXPOSE 8090
CMD python3 app.py
