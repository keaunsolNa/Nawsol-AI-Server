import os
from datetime import datetime, timedelta

import aiohttp


class DataGoClient:

    def __init__(self):
        self.data_go_key = os.getenv("DATA_GO_KEY")
        self.data_go_etf_end_point = os.getenv("DATA_GO_ETF_END_POINT")

    async def get_etf_data(self, start:str = None, end:str = None) -> list[dict]:
        if start is not None and end is not None:
            # start와 end를 datetime 객체로 변환
            start_date = datetime.strptime(start, "%Y%m%d")
            end_date = datetime.strptime(end, "%Y%m%d")
            
            results = []
            async with aiohttp.ClientSession() as session:
                # start부터 end까지 모든 날짜에 대해 반복
                current_date = start_date
                while current_date <= end_date:
                    today = current_date.strftime("%Y%m%d")
                    
                    base_url = (
                        f"{self.data_go_etf_end_point}?serviceKey={self.data_go_key}&"
                        f"numOfRows=10000&pageNo=1&resultType=json&basDt={today}"
                    )

                    async with session.get(f"{base_url}") as response:
                        if response.status != 200:
                            raise Exception(f"DataGo API Error {response.status}")
                        data = await response.json()
                        results.extend(data["response"]["body"]["items"]["item"])
                    
                    # 다음 날짜로 이동
                    current_date += timedelta(days=1)

            return results

        else:
            today = datetime.today().strftime("%Y%m%d")

            results = []
            async with aiohttp.ClientSession() as session:
                base_url = (
                    f"{self.data_go_etf_end_point}?serviceKey={self.data_go_key}&"
                    f"numOfRows=10000&pageNo=1&resultType=json&basDt={today}"
                )

                async with session.get(f"{base_url}") as response:
                    if response.status != 200:
                        raise Exception(f"DataGo API Error {response.status}")
                    data = await response.json()
                    results.extend(data["response"]["body"]["items"]["item"])

            return results
