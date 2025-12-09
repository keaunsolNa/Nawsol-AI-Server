import re
import html
import asyncio
from datetime import datetime
from typing import List, Optional
from email.utils import parsedate_to_datetime

import aiohttp

from news_info.domain.value_object.news_info import NewsInfo
from news_info.domain.value_object.news_item import NewsItem
from news_info.domain.value_object.news_source import NewsSource
from news_info.domain.value_object.timestamp import Timestamp
from news_info.infrastructure.api.naver_news_client import NaverNewsClient


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

def _strip_tags(text: str) -> str:
    return _TAG_RE.sub("", text or "").strip()

def _clean_text(text: str) -> str:
    return _WS_RE.sub(" ", html.unescape(_strip_tags(text))).strip()

def _parse_pubdate(pub_date_raw: str) -> datetime:
    if not pub_date_raw:
        return datetime.now()
    try:
        dt = parsedate_to_datetime(pub_date_raw)
        return dt.replace(tzinfo=None)
    except Exception:
        return datetime.now()

def _canonical_url(item: dict) -> str:
    return (item.get("originallink") or item.get("link") or "").strip()

_FINANCE_KEYWORDS = [
    "주식", "증시", "코스피", "코스닥", "나스닥", "다우", "s&p", "지수",
    "주가", "시총", "공매도", "거래량", "상승", "하락",
    "환율", "원달러", "달러", "엔화", "위안", "외환", "fx",
    "금리", "기준금리", "국채", "채권", "fomc", "cpi", "물가", "인플레이션",
    "etf", "etn", "펀드", "리츠", "reit", "배당", "실적",
    "반도체", "d램", "dram"
]

def _is_finance_article(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    return any(k.lower() in text for k in _FINANCE_KEYWORDS)

def _is_naver_news_url(url: str) -> bool:
    if not url:
        return False
    return ("n.news.naver.com" in url) or ("news.naver.com" in url)

# 네이버 뉴스 본문 영역 파싱 (레이아웃 변경 대비해 여러 셀렉터 시도)
def _extract_naver_news_content(page_html: str) -> Optional[str]:
    try:
        from bs4 import BeautifulSoup
    except Exception:
        # bs4 없으면 본문 파싱 정확도가 떨어져서 None 처리
        return None

    soup = BeautifulSoup(page_html, "html.parser")

    # 우선순위로 본문 후보 찾기
    node = soup.select_one("#dic_area") \
        or soup.select_one("#newsct_article") \
        or soup.select_one("#articleBodyContents")

    if not node:
        return None

    text = node.get_text(" ", strip=True)
    text = text.replace("\u200b", "")
    text = _WS_RE.sub(" ", text).strip()

    return text or None

async def _fetch_html(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None
            return await resp.text()
    except Exception:
        return None


class NaverNewsInfoAdapter:
    BRIEFING_QUERIES = ["환율", "금리", "코스피", "주식", "ETF"]

    def __init__(self):
        self.client = NaverNewsClient()

    async def fetch_latest_finance_news(
            self,
            limit: int = 10,
            display_per_query: int = 20,
            sort: str = "date",
            finance_only: bool = True,
            include_content: bool = False,
            require_content: bool = False,  # True면 content 없으면 제외(결과 개수 줄 수 있음)
    ) -> NewsInfo:
        # 1) 키워드 세트로 병렬 호출
        tasks = [
            self.client.search_news(query=q, display=display_per_query, start=1, sort=sort)
            for q in self.BRIEFING_QUERIES
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        raw_items: list[dict] = []
        for lst in results:
            raw_items.extend(lst or [])

        # 2) 중복 제거 (originallink 우선)
        deduped: list[dict] = []
        seen: set[str] = set()
        for it in raw_items:
            key = _canonical_url(it)
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(it)

        # 3) 금융 필터(옵션)
        if finance_only:
            filtered = []
            for it in deduped:
                t = _clean_text(it.get("title", ""))
                d = _clean_text(it.get("description", ""))
                if _is_finance_article(t, d):
                    filtered.append(it)
        else:
            filtered = deduped

        # 4) published_at 기준 최신순 정렬
        filtered.sort(
            key=lambda it: _parse_pubdate(it.get("pubDate", "")),
            reverse=True,
        )

        # 5) 본문 추출(옵션) — 너무 많이 긁지 않게 여유분만
        candidates = filtered[: max(limit * 4, limit)]  # 10개 뽑으려면 최대 40개만 본문 시도
        content_map: dict[int, Optional[str]] = {}

        if include_content and candidates:
            sem = asyncio.Semaphore(5)

            async def _fetch_one(idx: int, url: str, session: aiohttp.ClientSession):
                async with sem:
                    page_html = await _fetch_html(session, url)
                    if not page_html:
                        content_map[idx] = None
                        return
                    content_map[idx] = _extract_naver_news_content(page_html)

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                tasks2 = []
                for idx, it in enumerate(candidates):
                    url = it.get("link", "") or ""
                    if not _is_naver_news_url(url):
                        origin = it.get("originallink", "") or ""
                        url = origin if _is_naver_news_url(origin) else ""

                    if url:
                        tasks2.append(_fetch_one(idx, url, session))
                    else:
                        content_map[idx] = None

                if tasks2:
                    await asyncio.gather(*tasks2, return_exceptions=False)

        # 6) 도메인 변환 + limit 개수 채우기
        items: List[NewsItem] = []
        for idx, it in enumerate(candidates):
            title = _clean_text(it.get("title", ""))
            desc = _clean_text(it.get("description", ""))
            content = content_map.get(idx) if include_content else None

            if include_content and require_content and not content:
                continue

            items.append(
                NewsItem(
                    title=title,
                    description=desc,
                    content=content,
                    link=it.get("link", ""),
                    originallink=it.get("originallink", ""),
                    published_at=Timestamp(_parse_pubdate(it.get("pubDate", ""))),
                )
            )

            if len(items) >= limit:
                break

        return NewsInfo(
            items=items,
            source=NewsSource("NaverNewsAPI"),
            fetched_at=Timestamp(datetime.now()),
        )

    async def fetch_news_info(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date",
        finance_only: bool = True,
        include_content: bool = True,
        require_content: bool = True
    ) -> NewsInfo:
        raw_items = await self.client.search_news(query=query, display=display, start=start, sort=sort)

        # 1) 제목/요약 정리 후 금융 필터(옵션)
        if finance_only:
            filtered = []
            for it in raw_items:
                t = _clean_text(it.get("title", ""))
                d = _clean_text(it.get("description", ""))
                if _is_finance_article(t, d):
                    filtered.append(it)
        else:
            filtered = raw_items

        # 2) 본문 필요하면, 네이버 뉴스 URL만 추가로 HTML 가져와서 파싱
        content_map: dict[int, Optional[str]] = {}
        if include_content and filtered:
            sem = asyncio.Semaphore(5)

            async def _fetch_one(idx: int, url: str, session: aiohttp.ClientSession):
                async with sem:
                    page_html = await _fetch_html(session, url)
                    if not page_html:
                        content_map[idx] = None
                        return
                    content_map[idx] = _extract_naver_news_content(page_html)

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                tasks = []
                for idx, it in enumerate(filtered):
                    # 네이버 뉴스 링크 우선, 아니면 originallink가 네이버면 그걸 사용
                    url = it.get("link", "") or ""
                    if not _is_naver_news_url(url):
                        origin = it.get("originallink", "") or ""
                        url = origin if _is_naver_news_url(origin) else ""

                    if url:
                        tasks.append(_fetch_one(idx, url, session))
                    else:
                        content_map[idx] = None

                if tasks:
                    await asyncio.gather(*tasks)

        # 3) 도메인 변환
        items: List[NewsItem] = []
        for idx, item in enumerate(filtered):
            title = _clean_text(item.get("title", ""))
            desc = _clean_text(item.get("description", ""))
            content = content_map.get(idx) if include_content else None

            if include_content and require_content and not content:
                continue

            items.append(
                NewsItem(
                    title=title,
                    description=desc,
                    content=content,
                    link=item.get("link", ""),
                    originallink=item.get("originallink", ""),
                    published_at=Timestamp(_parse_pubdate(item.get("pubDate", ""))),
                )
            )

        # 본문 있는 기사 중 최대 10개만 반환
        if include_content:
            items = items[:10]

        return NewsInfo(
            items=items,
            source=NewsSource("NaverNewsAPI"),
            fetched_at=Timestamp(datetime.now()),
        )