FROM docker.io/pytorch/pytorch:2.7.1-cuda12.6-cudnn9-runtime

RUN apt-get update && \
    apt-get install -y build-essential gcc g++

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cu126

RUN mkdir -p /model/test /result /benchmark_lib

COPY models /models
COPY run /run

WORKDIR /
CMD ["python", "run/main.py"]