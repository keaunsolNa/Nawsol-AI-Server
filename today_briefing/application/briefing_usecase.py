
from typing import Dict, List
from datetime import datetime, timedelta

from community.infrastructure.repository.community_repository_impl import CommunityRepositoryImpl
from config.crypto import Crypto
from config.redis_config import get_redis
from ecos.infrastructure.api.ecos_client import EcosClient
from ecos.infrastructure.orm.exchange_rate import ExchangeType
from ecos.infrastructure.repository.ecos_repository_impl import EcosRepositoryImpl
from ieinfo.infrastructure.repository.ie_info_repository_impl import IEInfoRepositoryImpl
from ieinfo.infrastructure.orm.ie_info import IEType
from news_info.infrastructure.repository.news_info_repository_impl import NewsInfoRepositoryImpl
from recommendation.domain.service.card_news_service import CardNewsService
from today_briefing.domain.today_briefing_service import TodayBriefingService
from util.log.log import Log

logger = Log.get_logger()

class BriefingUseCase:

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.news_repository = NewsInfoRepositoryImpl.get_instance()
            self.community_repository = CommunityRepositoryImpl.get_instance()
            self.ecos_repository = EcosRepositoryImpl.get_instance()

    async def get_briefing_data_from_db(self) -> Dict:

        try:
            news_records = await self.news_repository.get_three_month_news_for_card_news()
            community_records = await self.community_repository.get_three_month_community_for_card_news()
            client = EcosClient()
            start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y%m%d")
            end_date = datetime.utcnow().strftime("%Y%m%d")

            exchange_rate = await client.get_exchange_rate(start_date, end_date)
            interest_rate = await client.get_interest_rate(start_date, end_date)

            logger.debug(f"news_recordse: {news_records}")

            valid_items = [item for item in exchange_rate if item.get("TIME")]

            if not valid_items:
                interest_data = []
            else:
                # 날짜 파싱
                for item in valid_items:
                    item["_parsed_time"] = datetime.strptime(item["TIME"], "%Y%m%d")

            # 최신 날짜 찾기
            latest_date = max(item["_parsed_time"] for item in valid_items)

            # 최신 날짜의 item만 filtering
            latest_items = [
                item for item in valid_items if item["_parsed_time"] == latest_date
            ]

            exchange_data = [
                {
                    "type_of_content": "EXCHANGE",
                    "key": ExchangeType(n.get("ITEM_CODE1")).name,
                    "value": n.get("DATA_VALUE")
                }
                for n in latest_items
            ]

            valid_items = [item for item in interest_rate if item.get("TIME")]

            if not valid_items:
                interest_data = []
            else:
                # 날짜 파싱
                for item in valid_items:
                    item["_parsed_time"] = datetime.strptime(item["TIME"], "%Y%m%d")

            # 최신 날짜 찾기
            latest_date = max(item["_parsed_time"] for item in valid_items)

            # 최신 날짜의 item만 filtering
            latest_items = [
                item for item in valid_items if item["_parsed_time"] == latest_date
            ]

            interest_data = [
                {
                    "type_of_content": "INTEREST",
                    "key": n.get("ITEM_NAME1"),
                    "value": n.get("DATA_VALUE")
                }
                for n in latest_items
            ]

            news_items = [
                {
                    "type_of_content": "NEWS",
                    "key": n.title,
                    "value": n.description,
                }
                for n in news_records
            ]

            # 커뮤니티 → 공통 dict
            community_items = [
                {
                    "type_of_content": "COMMUNITY",
                    "key": c.title,
                    "value": c.content[0:50],
                }
                for c in community_records
            ]

            combined = news_items + community_items + exchange_data + interest_data

            recommendation_result = await TodayBriefingService.make_today_briefing(
                briefing_data=combined
            )

            if recommendation_result.get("success"):
                recommended_card_news = recommendation_result.get("recommendation", [])

                return {
                    "success": True,
                    "recommended_briefing": recommended_card_news,
                }
            else:
                return recommendation_result
        except Exception as e:
            logger.error(f"Error in Briefing recommendation: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"브리핑 자료 생성 중 오류가 발생했습니다. {str(e)}"
            }