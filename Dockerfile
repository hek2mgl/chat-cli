FROM python:3.12

COPY . /opt/duckchat
RUN python -m venv /opt/duckchat/venv \
  && . /opt/duckchat/venv/bin/activate \
  && pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir /opt/duckchat

ENTRYPOINT ["/opt/duckchat/venv/bin/duckchat"]
