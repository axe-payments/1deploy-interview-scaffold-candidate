FROM python:3.12-slim

WORKDIR /code

# Runtime + test tooling, so `./scripts/test.sh` works without Python on your machine.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

# docker-compose.yml repeats this command (a Compose `command:` replaces CMD).
# --host 0.0.0.0 is required: uvicorn's default 127.0.0.1 bind is unreachable
# from the published host port and from the tunnel containers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
