"""微博 API 请求适配层 - 双方案策略"""

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import parse_qs, urlparse, unquote

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/15.0 Mobile/15E148 Safari/604.1"
)


@dataclass
class Topic:
    """超话信息"""
    title: str
    container_id: str
    scheme: str = ""


@dataclass
class CheckinResult:
    """签到结果"""
    topic_title: str
    status: str  # success / already / failed
    detail: str = ""


def _build_cookies(sub: str, subp: str, twm: str = "") -> str:
    """构建 Cookie 字符串"""
    parts = [f"SUB={sub}", f"SUBP={subp}"]
    if twm:
        parts.append(f"_T_WM={twm}")
    return "; ".join(parts)


def _get_api_params() -> dict:
    """获取微博 API 抓包参数"""
    try:
        return json.loads(settings.WEIBO_API_PARAMS)
    except Exception:
        return {}


class BaseProvider(ABC):
    """签到策略基类"""

    def __init__(self, sub: str, subp: str, twm: str = ""):
        self.cookie_str = _build_cookies(sub, subp, twm)
        self.api_params = _get_api_params()
        self.headers = {
            "User-Agent": MOBILE_UA,
            "Cookie": self.cookie_str,
        }

    @abstractmethod
    async def get_topics(self) -> List[Topic]:
        """获取所有关注的超话列表"""
        ...

    @abstractmethod
    async def checkin(self, topic: Topic) -> CheckinResult:
        """对一个超话执行签到"""
        ...


class CardlistProvider(BaseProvider):
    """
    方案 A: cardlist + page/button
    - GET /2/cardlist -> 提取 scheme -> 构造 request_url -> GET /2/page/button
    """

    CARDLIST_URL = "https://api.weibo.cn/2/cardlist"
    PAGE_BUTTON_URL = "https://api.weibo.cn/2/page/button"

    async def get_topics(self) -> List[Topic]:
        topics = []
        since_id = ""

        async with httpx.AsyncClient(timeout=15, headers=self.headers) as client:
            while True:
                params = {
                    **self.api_params,
                    "containerid": "100803_-_followsuper",
                    "fid": "100803_-_followsuper",
                    "page_type": "08",
                    "since_id": since_id,
                }
                try:
                    resp = await client.get(self.CARDLIST_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"获取超话列表失败: {e}")
                    break

                cards = data.get("cards", [])
                logger.info(f"CardlistProvider: 第{len(topics)//10+1}页, cards数量={len(cards)}")
                if not cards:
                    # 记录原始响应帮助排查
                    logger.info(f"CardlistProvider: 无cards返回, 原始响应keys={list(data.keys())}, ok={data.get('ok')}, msg={data.get('msg', '')}")
                    break

                for card in cards:
                    card_group = card.get("card_group", [])
                    for item in card_group:
                        card_type = item.get("card_type")
                        # card_type 可能是 int 或 str
                        if str(card_type) == "8":
                            scheme = item.get("scheme", "")
                            title = item.get("title_sub", "未知超话")
                            # 从 scheme 提取 containerid
                            cid = self._extract_containerid(scheme)
                            if cid:
                                topics.append(Topic(title=title, container_id=cid, scheme=scheme))
                            else:
                                logger.warning(f"CardlistProvider: 超话 [{title}] 无法提取containerid, scheme={scheme[:100]}")

                # 分页
                cardlist_info = data.get("cardlistInfo", {})
                new_since_id = cardlist_info.get("since_id", "")
                if not new_since_id or new_since_id == since_id:
                    break
                since_id = new_since_id

        logger.info(f"CardlistProvider: 获取到 {len(topics)} 个超话")
        return topics

    async def checkin(self, topic: Topic) -> CheckinResult:
        request_url = (
            f"http://i.huati.weibo.com/mobile/super/active_fcheckin"
            f"?cardid=bottom_one_checkin"
            f"&container_id={topic.container_id}"
            f"&pageid={topic.container_id}"
            f"&scheme_type=1"
        )

        params = {
            **self.api_params,
            "fid": "232478_-_one_checkin",
            "request_url": request_url,
        }

        try:
            async with httpx.AsyncClient(timeout=10, headers=self.headers) as client:
                resp = await client.get(self.PAGE_BUTTON_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            return self._parse_result(topic.title, data)
        except Exception as e:
            logger.error(f"签到失败 [{topic.title}]: {e}")
            return CheckinResult(topic_title=topic.title, status="failed", detail=str(e))

    @staticmethod
    def _extract_containerid(scheme: str) -> Optional[str]:
        """从 scheme URL 提取 containerid"""
        try:
            parsed = urlparse(scheme)
            qs = parse_qs(parsed.query)
            cid_list = qs.get("containerid", [])
            if cid_list:
                return cid_list[0]
            # 尝试从 fragment 提取
            if parsed.fragment:
                qs2 = parse_qs(parsed.fragment)
                cid_list2 = qs2.get("containerid", [])
                if cid_list2:
                    return cid_list2[0]
            # 尝试正则
            match = re.search(r"containerid=([^&]+)", scheme)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    @staticmethod
    def _parse_result(title: str, data: dict) -> CheckinResult:
        """解析签到响应"""
        msg = str(data.get("msg", "")).lower()
        result = data.get("result", None)

        if "已签" in msg or "already" in msg:
            return CheckinResult(topic_title=title, status="already", detail=msg)
        elif result == 1 or "签到成功" in msg or "success" in msg:
            return CheckinResult(topic_title=title, status="success", detail=msg)
        else:
            return CheckinResult(topic_title=title, status="failed", detail=msg or str(data))


class TopicsubProvider(BaseProvider):
    """
    方案 B: container_timeline_topicsub + page/button
    - POST /2/statuses/container_timeline_topicsub -> 提取 action/ext_uid
    - POST /2/page/button
    """

    TOPICSUB_URL = "https://api.weibo.cn/2/statuses/container_timeline_topicsub"
    PAGE_BUTTON_URL = "https://api.weibo.cn/2/page/button"

    @staticmethod
    def _extract_request_url(action: str) -> str:
        """从 action 中提取 request_url，兼容直接/嵌套两种格式。"""
        if not action:
            return ""
        try:
            parsed = urlparse(action)
            qs = parse_qs(parsed.query)
            req = (qs.get("request_url") or [""])[0]
            if req:
                return unquote(req)
        except Exception:
            pass
        return action

    @staticmethod
    def _extract_container_id(item_data: dict, button: dict) -> str:
        """提取 container_id/ext_uid。"""
        params = button.get("params", {}) if isinstance(button, dict) else {}
        return (
            item_data.get("container_id", "")
            or params.get("container_id", "")
            or params.get("ext_uid", "")
        )

    async def get_topics(self) -> List[Topic]:
        topics = []
        since_id = ""

        async with httpx.AsyncClient(timeout=15, headers=self.headers) as client:
            while True:
                params = {**self.api_params}
                body = {
                    "flowId": "232478_-_one_checkin",
                    "since_id": since_id,
                }
                try:
                    resp = await client.post(self.TOPICSUB_URL, params=params, json=body)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"获取超话列表失败: {e}")
                    break

                items = data.get("items", [])
                logger.info(f"TopicsubProvider: items数量={len(items)}")
                if not items:
                    logger.info(f"TopicsubProvider: 无items返回, 原始响应keys={list(data.keys())}, ok={data.get('ok')}, msg={data.get('msg', '')}")
                    break

                for item_group in items:
                    sub_items = item_group.get("items", [])
                    for item in sub_items:
                        item_data = item.get("data", {})
                        buttons = item_data.get("buttons", [])
                        title = item_data.get("title_sub", "未知超话")

                        for btn in buttons:
                            params = btn.get("params", {}) if isinstance(btn, dict) else {}
                            action = btn.get("action", "") or params.get("action", "")
                            cid = self._extract_container_id(item_data, btn)
                            if action and cid:
                                request_url = self._extract_request_url(action)
                                topics.append(Topic(title=title, container_id=cid, scheme=request_url))
                                break

                # 分页
                new_since_id = data.get("since_id", "")
                if not new_since_id or new_since_id == since_id:
                    break
                since_id = new_since_id

        logger.info(f"TopicsubProvider: 获取到 {len(topics)} 个超话")
        return topics

    async def checkin(self, topic: Topic) -> CheckinResult:
        # 从 action/scheme 中提取 request_url
        request_url = topic.scheme

        # 兼容微博接口变更: 同时透传 query 与 body
        params = {
            **self.api_params,
            "fid": "232478_-_one_checkin",
            "request_url": request_url,
            "ext_uid": topic.container_id,
        }
        body = {
            "fid": "232478_-_one_checkin",
            "request_url": request_url,
            "ext_uid": topic.container_id,
        }

        try:
            async with httpx.AsyncClient(timeout=10, headers=self.headers) as client:
                resp = await client.post(self.PAGE_BUTTON_URL, params=params, json=body)
                resp.raise_for_status()
                data = resp.json()

            result = data.get("result")
            msg = str(data.get("msg", ""))

            if "已签" in msg:
                return CheckinResult(topic_title=topic.title, status="already", detail=msg)
            elif result == 1:
                return CheckinResult(topic_title=topic.title, status="success", detail=msg)
            else:
                return CheckinResult(topic_title=topic.title, status="failed", detail=msg or str(data))

        except Exception as e:
            logger.error(f"签到失败 [{topic.title}]: {e}")
            return CheckinResult(topic_title=topic.title, status="failed", detail=str(e))


class MWeiboProvider(BaseProvider):
    """
    方案 C: m.weibo.cn 网页接口
    - GET /api/container/getIndex?containerid=100803_-_followsuper
    - 从 cards/card_group 提取 buttons(name=签到) 的 scheme
    - GET /api/container/button?... 执行签到
    """

    GETINDEX_URL = "https://m.weibo.cn/api/container/getIndex"
    BASE_URL = "https://m.weibo.cn"

    def __init__(self, sub: str, subp: str, twm: str = ""):
        super().__init__(sub, subp, twm)
        self.headers.update(
            {
                "Referer": "https://m.weibo.cn/p/index?containerid=100803_-_followsuper",
                "Accept": "application/json, text/plain, */*",
            }
        )

    async def get_topics(self) -> List[Topic]:
        topics: List[Topic] = []
        since_id = ""

        async with httpx.AsyncClient(timeout=15, headers=self.headers) as client:
            while True:
                params = {"containerid": "100803_-_followsuper"}
                if since_id:
                    params["since_id"] = since_id

                try:
                    resp = await client.get(self.GETINDEX_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"MWeiboProvider 获取超话列表失败: {e}")
                    break

                if data.get("ok") != 1:
                    logger.info(
                        "MWeiboProvider: 接口返回非ok, "
                        f"ok={data.get('ok')}, msg={data.get('msg', '')}"
                    )
                    break

                payload = data.get("data", {})
                cards = payload.get("cards", [])
                logger.info(f"MWeiboProvider: cards数量={len(cards)}")
                if not cards:
                    break

                for card in cards:
                    card_group = card.get("card_group", [])
                    if card_group:
                        for item in card_group:
                            topic = self._parse_topic_item(item)
                            if topic:
                                topics.append(topic)
                    else:
                        topic = self._parse_topic_item(card)
                        if topic:
                            topics.append(topic)

                new_since_id = payload.get("cardlistInfo", {}).get("since_id", "")
                if not new_since_id or new_since_id == since_id:
                    break
                since_id = new_since_id

        logger.info(f"MWeiboProvider: 获取到 {len(topics)} 个超话")
        return topics

    def _parse_topic_item(self, item: dict) -> Optional[Topic]:
        title = item.get("title_sub") or item.get("title") or "未知超话"
        buttons = item.get("buttons", []) or []
        if not buttons:
            return None

        # 优先找可签到按钮
        for b in buttons:
            name = str(b.get("name", "")).strip()
            scheme = b.get("scheme", "")
            if name == "签到" and scheme:
                return Topic(title=title, container_id="", scheme=scheme)

        # 无可签到按钮但存在“已签/明日再来”等状态时，保留为已签到项
        for b in buttons:
            name = str(b.get("name", "")).strip()
            if name in ("已签", "已签到", "明日再来"):
                return Topic(title=title, container_id="", scheme="")

        return None

    async def checkin(self, topic: Topic) -> CheckinResult:
        if not topic.scheme:
            return CheckinResult(topic_title=topic.title, status="already", detail="已签到或明日再来")

        # 相对路径补全
        sign_url = topic.scheme
        if sign_url.startswith("/"):
            sign_url = f"{self.BASE_URL}{sign_url}"

        try:
            async with httpx.AsyncClient(timeout=10, headers=self.headers) as client:
                resp = await client.get(sign_url)
                resp.raise_for_status()
                data = resp.json()

            ok = data.get("ok")
            msg = str((data.get("data") or {}).get("msg") or data.get("msg") or "")

            if "已签" in msg or "明日再来" in msg:
                return CheckinResult(topic_title=topic.title, status="already", detail=msg)

            if ok == 1 and ("成功" in msg or "签到" in msg or msg == ""):
                return CheckinResult(topic_title=topic.title, status="success", detail=msg or "签到成功")

            return CheckinResult(topic_title=topic.title, status="failed", detail=msg or str(data))

        except Exception as e:
            logger.error(f"MWeiboProvider 签到失败 [{topic.title}]: {e}")
            return CheckinResult(topic_title=topic.title, status="failed", detail=str(e))


def get_provider(sub: str, subp: str, twm: str = "", provider_name: str = "") -> BaseProvider:
    """工厂函数: 获取签到策略 Provider"""
    name = provider_name or settings.CHECKIN_PROVIDER

    if name == "topicsub":
        return TopicsubProvider(sub, subp, twm)
    if name == "mweibo":
        return MWeiboProvider(sub, subp, twm)
    else:
        return CardlistProvider(sub, subp, twm)
