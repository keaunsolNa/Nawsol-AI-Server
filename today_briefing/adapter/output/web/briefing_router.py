from fastapi import APIRouter
from today_briefing.application.briefing_usecase import BriefingUseCase
from util.log.log import Log

logger = Log.get_logger()
today_briefing_router = APIRouter(tags=["today_briefing"])
usecase = BriefingUseCase.get_instance()

@today_briefing_router.get("/today-briefing-info")
async def get_today_briefing_info():

    try:
        result = await usecase.get_briefing_data_from_db()

        if isinstance(result, dict):
            source = result.get("source", "gpt")
            items = result.get("recommended_briefing", [])
        else:
            source = getattr(result, "source", "gpt")
            items = getattr(result, "recommended_briefing", [])

        return {
            "source": source,
            "items": items
        }

    except Exception as e:
        logger.error(f"Error in Briefing recommendation: {str(e)}")
        return {
            "source": "error",
            "items": []
        }
