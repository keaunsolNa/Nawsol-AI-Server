"""
사용자 맞춤형 카드 뉴스 AI 서비스
사용자의 자산 정보를 기반으로 적합한 커뮤니티/네이버 뉴스 기사를 검색하여
카드뉴스 형태로 반환한다.
"""
import asyncio
from typing import Dict, List

from click import prompt
from openai import OpenAI
from util.log.log import Log

logger = Log.get_logger()
client = OpenAI()

class CardNewsService:
    """CardNews 추천 AI 서비스"""

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

    @staticmethod
    def _build_financial_profile(
            income_data: Dict[str, int],
            expense_data: Dict[str, int],
            total_income: int,
            total_expense: int,
            surplus: int
    ) -> str:
        """재무 프로필 문자열 생성"""
        profile_parts = []

        # 기본 재무 정보
        profile_parts.append(f"📊 재무 요약")
        profile_parts.append(f"- 총 소득: {total_income:,}원")
        profile_parts.append(f"- 총 지출: {total_expense:,}원")
        profile_parts.append(f"- 여유 자금: {surplus:,}원")
        profile_parts.append(f"- 저축률: {(surplus / total_income * 100):.1f}%" if total_income > 0 else "- 저축률: 0%")

        # 소득 상세
        if income_data:
            profile_parts.append(f"\n💰 소득 내역")
            for key, value in sorted(income_data.items(), key=lambda x: x[1], reverse=True)[:5]:
                profile_parts.append(f"- {key}: {value:,}원")

        # 지출 상세
        if expense_data:
            profile_parts.append(f"\n💸 주요 지출")
            for key, value in sorted(expense_data.items(), key=lambda x: x[1], reverse=True)[:5]:
                profile_parts.append(f"- {key}: {value:,}원")

        return "\n".join(profile_parts)

    @staticmethod
    def _build_card_news(community_and_news_data: List[Dict]):
        """ Community, news_info 문자열 생성"""
        if not community_and_news_data:
            return "저장된 커뮤니티 크롤링 정보 혹은 뉴스 데이터가 없습니다."

        card_news = [f"분석 가능한 카드 뉴스 목록 ({len(community_and_news_data)}개"]

        for idx, news in enumerate(community_and_news_data, 1):
            title = news.get('title', 'N/A')
            type_of_content = news.get('type_of_content', 'N/A')
            provider = news.get('provider', 'N/A')
            content = news.get('content', 'N/A')
            link = news.get('link', 'N/A')

            card_news.append(
                f"{idx}. {title} | "
                f"타입: {type_of_content} |"
                f"제공자: {provider} | "
                f"본문: {content} | "
                f"링크: {link} | "
            )

        return "\n".join(card_news)

    @classmethod
    async def recommend_card_news(
        cls,
        income_data: Dict[str, int],
        expense_data: Dict[str, int],
        total_income: int,
        total_expense: int,
        surplus: int,
        community_and_news_data: List[Dict]
    ) -> Dict:
        """
            사용자 재무 정보를 기반으로 카드 뉴스 추천

            Args:
                income_data: 소득 데이터
                expense_data: 지출 데이터
                total_income: 총 소득
                total_expense: 총 지출
                surplus: 여유 자금
                community_and_news_data: 카드뉴스 데이터 목록

            Returns:
                추천 결과 딕셔너리
        """
        try:
            financial_profile = cls._build_financial_profile(
                income_data, expense_data, total_income, total_expense, surplus
            )

            card_news_list = cls._build_card_news(community_and_news_data)

            prompt_part1 = F""" 당신은 전문 기자입니다. 사용자의 재무 상황을 분석하고, 주어진 데이터를 통해 적합한 커뮤니티 게시글과 뉴스 정보({card_news_list}를 추천해주세요. 데이터는 유사도가 높은 순서 (사용자의 소비 목록과 일치하는 단어 비중)로 선정합니다.

## 사용자 재무 정보
{financial_profile}

## 분석 가능한 커뮤니티와 뉴스 기사 목록
{card_news_list}

---

## 추천 요청사항
다음 형식으로 ** 정확히 5개의 카드 뉴스**를 추천해주세요:

### 1. 재무 분석 요약
- 사용자의 재무 상태를 간단히 분석 (3-4문장)
- 월 투자 가능 금액 추정
- 투자 성향 평가"""

            # AI 프롬프트 작성 (2부)
            prompt_part2 = """

### 2. 카드 뉴스 추천

##[추천 1] 카드뉴스명**
- 추천 이유: (2-3문장)
- 사용자의 소비 목록과 일치하는 단어 비중: X%
- 기사 제목
- 기사 요약(description)
- 기사 링크             

##[추천 2] 카드뉴스명**
- 추천 이유: (2-3문장)
- 사용자의 소비 목록과 일치하는 단어 비중: X%
- 기사 제목
- 기사 요약(description)
- 기사 링크             

##[추천 3] 카드뉴스명**
- 추천 이유: (2-3문장)
- 사용자의 소비 목록과 일치하는 단어 비중: X%
- 기사 제목
- 기사 요약(description)
- 기사 링크             

##[추천 4] 카드뉴스명**
- 추천 이유: (2-3문장)
- 사용자의 소비 목록과 일치하는 단어 비중: X%
- 기사 제목
- 기사 요약(description)
- 기사 링크     
        
##[추천 5] 카드뉴스명**
- 추천 이유: (2-3문장)
- 사용자의 소비 목록과 일치하는 단어 비중: X%
- 기사 제목
- 기사 요약(description)
- 기사 링크             
---

** 중요 규칙:**
1. 카드 뉴스 목록은 반드시 제공된 목록에서만 선택
2. 구체적인 수치와 근거 제시
3. 전문적이지만 이해하기 쉬운 설명
4. 과장되지 않은 현실적인 조언
5. 마크다운 형식 사용 금지 (일반 텍스트로만 작성)
"""
            prompt = prompt_part1 + prompt_part2

            # GPT 호출
            logger.info("Calling GPT for Card News recommendation...")
            recommendation = await cls._call_gpt(prompt)

            logger.info(f"Card News recommendation generated (length: {len(recommendation)})")

            return {
                "success": True,
                "financial_summary": {
                    "total_income": total_income,
                    "total_expense": total_expense,
                    "surplus": surplus,
                    "saving_rate": round(surplus / total_income * 100, 1) if total_income > 0 else 0,
                },
                "recommendation": recommendation,
                "card_news_count": len(community_and_news_data)
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

