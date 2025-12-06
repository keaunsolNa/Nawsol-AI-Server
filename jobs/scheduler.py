from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def run_scheduler_etf():
    print("TEST")

async def main():
    scheduler = AsyncIOScheduler()
    cron_etf_hour = os.getenv("CRON_ETF_HOUR", "03")
    cron_etf_minute = os.getenv("CRON_ETF_MINUTE", "00")
    trigger = CronTrigger(hour=cron_etf_hour, minute=cron_etf_minute, timezone="Asia/Seoul")
    scheduler.add_job(run_scheduler_etf, trigger)
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())