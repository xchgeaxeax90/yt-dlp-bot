FROM python:3.13

RUN apt update && apt install -y ffmpeg && \
  apt clean all && rm -rf /var/lib/apt/lists*

WORKDIR /workdir

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
