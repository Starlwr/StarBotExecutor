import asyncio
import platform

from .core.executor import executor

if 'windows' in platform.system().lower():
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
