import asyncio
from typing import Dict, List

from click import prompt
from openai import OpenAI
from util.log.log import Log

logger = Log.get_logger()
client = OpenAI()

class TodayBriefingService:

    @staticmethod
    async def _call_gpt(prompt: str, max_tokens: int = 2000) -> str:
        """GPT API 비동기 호출"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            ).choices[0].message.content
        )

    """
        당일의 환율, 금리, 금융 기사, 커뮤니티 정보를 취합하여 요약된 브리핑 정보를 반환한다.
    """
    @staticmethod
    def _build_today_briefing(briefing_data: List[Dict]):

        if not briefing_data:
            return "저장된 데이터가 없습니다."

        lines = [f"분석 가능한 정보 취합 목록 ({len(briefing_data)}개)"]

        for idx, briefing in enumerate(briefing_data, 1):
            if idx > 30:
                break
            if isinstance(briefing, dict):
                type_of_content = briefing.get('type_of_content', 'N/A')
                key = briefing.get('key', 'N/A')
                value = briefing.get('value', 'N/A')
                if isinstance(value, str):
                    value = value[:300]
            elif isinstance(briefing, str):
                type_of_content = 'RAW'
                key = ''
                value = briefing[:300]
            else:
                type_of_content = 'N/A'
                key = ''
                value = str(briefing)[:300]

            lines.append(f"{idx}. {type_of_content} | key: {key} | value: {value} |")

        return "\n".join(lines)

    @classmethod
    async def make_today_briefing(
            cls,
            briefing_data: List[Dict]
   ) -> Dict:
        try:
            total_items = len(briefing_data) if briefing_data is not None else 0

            # 문자열 브리핑 생성 (원본 briefing_data는 그대로)
            briefing_text = cls._build_today_briefing(briefing_data)

            prompt = F""" 당신은 전문 기자입니다. 주어진 금리, 환율, 금융기사, 커뮤니티 게시글을 분석하고, 주어진 데이터를 통해 당일의 주요 금융 소식에 대한 브리핑 정보를 만들어주세요.

## 주어진 데이터
{briefing_data}

type_of_content 는 데이터의 종류를 뜻합니다. 
INTEREST : 금리
EXCHANGE : 환율
COMMUNITY : 커뮤니티 게시글
NEWS : 인터넷 뉴스

key 는 데이터의 키 값입니다.
INTEREST : 금리 종류
EXCHANGE : 달러/옌/유로
COMMUNITY: 게시글 제목
NEWS: 뉴스 제목

value 는 데이터의 값입니다.
INTEREST : 금리 값
EXCHANGE : 원화 대비 환율
COMMUNITY : 게시글 본문
NEWS: 뉴스 본문
 
---

## 추천 요청사항
다음 형식으로 ** 브리핑 자료 ** 형태를 작성해주세요:

### '오늘날짜' 주요 금융 정보 브리핑
- 금리 동향
- 환율 동향
- 금융기사(당일 데이터가 주어짐) 주요 소식
- 커뮤니티(당일 데이터가 주어짐) 주요 소식

---
** 중요 규칙:**
1. 브리핑 정보는 반드시 제공된 목록에서만 선택
2. 구체적인 수치와 근거 제시
3. 전문적이지만 이해하기 쉬운 설명
4. 과장되지 않은 현실적인 조언
5. 마크다운 형식 사용 금지 (일반 텍스트로만 작성)
"""

            # GPT 호출
            logger.info("Calling GPT for Card News recommendation...")
            recommendation = await cls._call_gpt(prompt)
            logger.info(f"Card News recommendation generated (length: {len(recommendation)})")

            return {
                "success": True,
                "recommendation": recommendation,
                "briefing_data_count": total_items
            }

        except Exception as e:
            logger.error(f"Error in Card News recommendation: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "message": "카드 뉴스 추천 중 오류가 발생했습니다."
            }
