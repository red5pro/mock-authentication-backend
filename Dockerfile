FROM python:3.12-slim

LABEL maintainer="Red5 Pro <support@red5.net>"
LABEL description="Mock RoundTrip Authentication backend for Red5 Pro"

# Non-root user
RUN groupadd --gid 1000 mockauth \
 && useradd  --uid 1000 --gid mockauth --shell /bin/false mockauth

WORKDIR /app

COPY server.py .

RUN mkdir logs && chown mockauth:mockauth logs

USER mockauth

ENV MOCK_AUTH_HOST=0.0.0.0 \
    MOCK_AUTH_PORT=3000 \
    MOCK_AUTH_URL_RESOURCE="" \
    MOCK_AUTH_LOG_DIR=logs \
    MOCK_AUTH_LOG_LEVEL=INFO

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/')" || exit 1

ENTRYPOINT ["python3", "server.py"]
