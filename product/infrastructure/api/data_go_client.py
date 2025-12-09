import os
from datetime import datetime

import aiohttp


class DataGoClient:

    def __init__(self):
        self.data_go_key = os.getenv("DATA_GO_KEY")
        self.data_go_etf_end_point = os.getenv("DATA_GO_ETF_END_POINT")

    async def get_etf_data(self) -> list[dict]:
        # today = datetime.today().strftime("%Y%m%d")
        today=20251205
        results = []
        async with aiohttp.ClientSession() as session:
            base_url = (
                f"{self.data_go_etf_end_point}?serviceKey={self.data_go_key}&"
                f"numOfRows=10000&pageNo=1&resultType=json&basDt={today}"
            )

            async with session.get(f"{base_url}") as response:
                print("response:::", response)
                if response.status != 200:
                    raise Exception(f"DataGo API Error {response.status}")
                data = await response.json()
                print("data:::::::;::", data)
                results.extend(data["response"]["body"]["items"]["item"])

        return results
