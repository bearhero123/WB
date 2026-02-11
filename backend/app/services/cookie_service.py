"""Cookie 有效性校验服务"""

import logging
from typing import Tuple, Optional

import httpx

logger = logging.getLogger(__name__)

WEIBO_CONFIG_URL = "https://m.weibo.cn/api/config"
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/15.0 Mobile/15E148 Safari/604.1"
)


async def validate_cookie(sub: str, subp: str, twm: str = "") -> Tuple[bool, Optional[dict]]:
    """
    校验微博 Cookie 是否有效

    返回:
        (is_valid, user_info)
        - is_valid: Cookie 是否有效
        - user_info: 有效时返回用户信息 dict, 无效时返回 None
    """
    if not sub or not subp:
        return False, None

    cookie_str = f"SUB={sub}; SUBP={subp}"
    if twm:
        cookie_str += f"; _T_WM={twm}"

    headers = {
        "User-Agent": MOBILE_UA,
        "Cookie": cookie_str,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(WEIBO_CONFIG_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        config_data = data.get("data", {})
        is_login = config_data.get("login", False)

        if is_login:
            user_info = {
                "uid": config_data.get("uid", ""),
                "nick": config_data.get("user", {}).get("screen_name", ""),
            }
            return True, user_info
        else:
            return False, None

    except Exception as e:
        logger.error(f"Cookie 校验失败: {e}")
        return False, None
