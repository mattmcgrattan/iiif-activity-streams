FROM ubuntu
RUN apt-get -y update && apt-get install -y python-pip python-dev build-essential

COPY activity_streams.py /opt/activity_streams/
COPY docker_settings.py /opt/activity_streams/settings.py

COPY requirements.txt /opt/activity_streams/.

WORKDIR /opt/activity_streams/

RUN pip install uwsgi

RUN pip install -r requirements.txt


# Expose port 8000 for uwsgi

EXPOSE 8000

ENTRYPOINT ["uwsgi", "--http", "0.0.0.0:8000", "--module", "activity_streams:app", "--processes", "1", "--threads", "8"]