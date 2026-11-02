"""Command-line entry point for durable webhook processing."""

import asyncio

from .core.database import engine, init_db
from .services.outbox_worker import OutboxWorker


async def main() -> None:
    await init_db()
    worker = OutboxWorker()
    try:
        await worker.run_forever()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
