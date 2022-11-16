FROM python:3.9

RUN mkdir -p /home
WORKDIR /home

COPY app /home/app
COPY golmi /home/golmi
COPY requirements.txt /home/
COPY run.py /home/

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "run.py"]