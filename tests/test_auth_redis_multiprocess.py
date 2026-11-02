"""Cross-process auth checks against the CI Redis service."""

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from redis import Redis
from sqlalchemy.ext.asyncio import create_async_engine

from backend.core.database import Base
from backend.security.passwords import hash_password


pytestmark = pytest.mark.integration


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def _wait_until_ready(base_url: str, process: subprocess.Popen, log_path: Path) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"API process exited early; logs:\n{log_path.read_text()}")
        try:
            response = httpx.get(f"{base_url}/health", timeout=0.5)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise AssertionError(f"API process did not become ready; logs:\n{log_path.read_text()}")


def test_redis_auth_state_is_shared_between_api_processes(tmp_path: Path) -> None:
    if os.getenv("RUN_REDIS_MULTIPROCESS_TESTS") != "1":
        pytest.skip("set RUN_REDIS_MULTIPROCESS_TESTS=1 to run the Redis process test")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/15")
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    redis_client.flushdb()

    username = "multi-process-ci-operator"
    password = "multi-process-ci-test-password"
    shared_secret = "test-only-shared-session-signing-secret"
    db_path = tmp_path / "auth-multiprocess.db"
    database_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"

    async def prepare_database() -> None:
        engine = create_async_engine(database_url)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(prepare_database())

    child_env = os.environ.copy()
    child_env.update(
        {
            "DATABASE_URL": database_url,
            "REDIS_URL": redis_url,
            "OPERATOR_USERNAME": username,
            "OPERATOR_PASSWORD_HASH": hash_password(password),
            "SESSION_SECRET_KEY": shared_secret,
            "SESSION_COOKIE_SECURE": "false",
            "CORS_ALLOWED_ORIGINS": "http://localhost:3000",
        }
    )

    root = Path(__file__).resolve().parents[1]
    processes: list[subprocess.Popen] = []
    log_paths = [tmp_path / "api-a.log", tmp_path / "api-b.log"]
    try:
        for log_path in log_paths:
            port = _free_port()
            with log_path.open("w", encoding="utf-8") as output:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "backend.api.main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                    ],
                    cwd=root,
                    env=child_env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                )
            processes.append(process)
            log_path.with_suffix(".port").write_text(str(port), encoding="ascii")

        ports = [int(path.with_suffix(".port").read_text(encoding="ascii")) for path in log_paths]
        base_a, base_b = (f"http://127.0.0.1:{port}" for port in ports)
        for base_url, process, log_path in zip((base_a, base_b), processes, log_paths):
            _wait_until_ready(base_url, process, log_path)

        with httpx.Client(timeout=10) as client_a, httpx.Client(timeout=10) as client_b:
            login = client_a.post(
                f"{base_a}/api/v1/auth/login",
                json={"username": username, "password": password},
            )
            assert login.status_code == 200, login.text
            client_b.cookies.update(client_a.cookies)
            assert client_b.get(f"{base_b}/api/v1/auth/me").json() == {"username": username}
            assert client_b.get(f"{base_b}/api/v1/events").status_code == 200

            for _ in range(5):
                failed = client_a.post(
                    f"{base_a}/api/v1/auth/login",
                    json={"username": username, "password": "incorrect-password"},
                )
                assert failed.status_code == 401, failed.text
            throttled = client_b.post(
                f"{base_b}/api/v1/auth/login",
                json={"username": username, "password": "incorrect-password"},
            )
            assert throttled.status_code == 429
            assert int(throttled.headers["Retry-After"]) > 0

            logout = client_b.post(
                f"{base_b}/api/v1/auth/logout",
                headers={"X-CSRF-Token": client_a.cookies["hub_csrf"]},
            )
            assert logout.status_code == 200, logout.text
            assert client_a.get(f"{base_a}/api/v1/auth/me").status_code == 401
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        redis_client.flushdb()
        redis_client.close()
