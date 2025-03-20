FROM python:3.12

COPY . /opt/chatcli
RUN python -m venv /opt/chatcli/venv \
  && . /opt/chatcli/venv/bin/activate \
  && pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir /opt/chatcli

ENTRYPOINT ["/opt/chatcli/venv/bin/chatcli"]
