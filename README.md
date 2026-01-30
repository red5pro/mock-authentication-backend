# Mock Authentication Backend

A single-file Python 3 server that implements the RoundTrip Authentication (RTA) API expected by Red5 Pro's `RoundTripAuthValidator`. It approves all well-formed requests unconditionally -- no real credential validation is performed.

Use it during development and integration testing to confirm that Red5 Pro is correctly forwarding authentication requests, without needing a production auth system.

## What it does

The server exposes five endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Browser test page with validate/invalidate forms |
| `/logIn` | POST | Returns hardcoded streaming credentials |
| `/validateCredentials` | POST | Approves publishers and subscribers, denies unknown types |
| `/invalidateCredentials` | POST | Always returns `{"result": true}` |
| `/webhook` | POST | Logs the request body and returns `{}` |

Publishers get back `{"result": true, "url": ""}` (the `url` value is configurable). Subscribers get `{"result": true}`. Anything else gets `{"result": false}`.

No external dependencies -- stdlib only, runs on any system with Python 3.8+.

## Quick start

```bash
python3 server.py
```

Open http://localhost:3000 in a browser to use the test forms, or hit the endpoints with curl:

```bash
# Validate a publisher
curl -s -X POST http://localhost:3000/validateCredentials \
  -H "Content-Type: application/json" \
  -d '{"type":"publisher","username":"user1","password":"pass1","streamID":"stream1"}'
# {"result": true, "url": ""}

# Validate a subscriber
curl -s -X POST http://localhost:3000/validateCredentials \
  -H "Content-Type: application/json" \
  -d '{"type":"subscriber","username":"user1","password":"pass1","streamID":"stream1"}'
# {"result": true}

# Invalidate (publisher disconnect)
curl -s -X POST http://localhost:3000/invalidateCredentials \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass1","streamID":"stream1"}'
# {"result": true}
```

Stop the server with Ctrl-C. It handles SIGTERM and SIGINT for clean shutdown.

## Configuration

All settings are via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_AUTH_HOST` | `0.0.0.0` | Bind address |
| `MOCK_AUTH_PORT` | `3000` | Listen port |
| `MOCK_AUTH_URL_RESOURCE` | `""` | URL returned to publishers (stored as `signedURL` on the Red5 Pro connection) |
| `MOCK_AUTH_LOG_DIR` | `logs` | Directory for rolling log files |
| `MOCK_AUTH_LOG_MAX_BYTES` | `10485760` | Max size per log file (10 MB) |
| `MOCK_AUTH_LOG_BACKUP_COUNT` | `5` | Number of rotated log files to keep |
| `MOCK_AUTH_LOG_LEVEL` | `INFO` | Log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `MOCK_AUTH_PID_FILE` | `""` | Write PID to this file if set |

Example:

```bash
MOCK_AUTH_PORT=8080 MOCK_AUTH_LOG_LEVEL=DEBUG python3 server.py
```

## Install as a systemd service

1. Copy the server to its install location:

```bash
sudo mkdir -p /opt/mock-auth
sudo cp server.py /opt/mock-auth/
```

2. Create the log directory:

```bash
sudo mkdir -p /var/log/mock-auth
```

3. Install the unit file:

```bash
sudo cp systemd/mock-auth.service /etc/systemd/system/
```

4. Edit the unit file if you need to change the port, bind address, or log directory:

```bash
sudo systemctl edit mock-auth   # override specific Environment= lines
```

5. Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mock-auth
sudo systemctl start mock-auth
```

6. Check status and follow logs:

```bash
sudo systemctl status mock-auth
sudo journalctl -u mock-auth -f
```

The service restarts automatically on failure (10-second delay).

## Docker

### Build the image

```bash
docker build -t mock-auth .
```

### Run a container

```bash
docker run -d --name mock-auth -p 3000:3000 mock-auth
```

Override settings with `-e`:

```bash
docker run -d --name mock-auth \
  -p 8080:8080 \
  -e MOCK_AUTH_PORT=8080 \
  -e MOCK_AUTH_LOG_LEVEL=DEBUG \
  mock-auth
```

### Check health and logs

```bash
docker ps                      # HEALTHCHECK status in the STATUS column
docker logs -f mock-auth       # stream stdout logs
```

### Stop and remove

```bash
docker stop mock-auth
docker rm mock-auth
```

## Connecting to Red5 Pro

Point the `RoundTripAuthValidator` at this server in your webapp's `red5-web.xml`:

```xml
<bean id="roundTripValidator"
      class="com.red5pro.server.plugin.simpleauth.datasource.impl.roundtrip.RoundTripAuthValidator"
      init-method="initialize">
    <property name="adapter" ref="web.handler" />
    <property name="context" ref="web.context" />
    <property name="protocol" value="http://" />
    <property name="host" value="localhost" />
    <property name="port" value="3000" />
    <property name="validateCredentialsEndPoint" value="/validateCredentials" />
    <property name="invalidateCredentialsEndPoint" value="/invalidateCredentials" />
</bean>
```

The validator enforces a 9-second HTTP timeout. This server responds synchronously and immediately, well within that window.
