from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI

from api._test.router import router as testing_router
from api.account.router import router as account_router

from config import crons
from utils.logger import logger
from _services.redis.service import RedisClient


api_app = FastAPI()

Schedule: AsyncIOScheduler = None

async def startup_api():
    await RedisClient().delete_pattern('*')
    # Initialize Cron Jobs
    global Schedule
    try:
        jobstores = {
            'default': MemoryJobStore()
        }
        Schedule = AsyncIOScheduler(jobstores=jobstores)
        Schedule.start()
        for index, job in enumerate(crons.JOB_SCHEDULE):
            logger.info(Schedule.add_job(**job, id=str(index)))
        logger.info("Created Schedule Object")

    except Exception as e:
        logger.error("Unable to Create Schedule", e)


async def shutdown_api():
    global Schedule
    Schedule.shutdown()
    logger.info("Disable Schedule")


api_app.include_router(testing_router, tags=["testing"], prefix="/testing")
api_app.include_router(account_router, tags=["account"], prefix="/account")





