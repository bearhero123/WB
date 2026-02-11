核心逻辑整理（通过 Cookie 一键签到）

1) 加载 Cookie
- 从 cookie.json 读取 cookie_dict（至少要有 SUB）
- 写入 requests.Session().cookies，用于后续所有请求

2) 验证登录
- 请求 https://m.weibo.cn/api/config
- data.login 为 true 即 Cookie 有效

3) 获取关注超话列表（分页）
- 请求 https://m.weibo.cn/api/container/getIndex
- containerid=100803_-_followsuper
- 读取 data.cards 与 cardlistInfo.since_id，直到 since_id 为空

4) 判断是否可签到
- 每个超话卡片里有 buttons
- button.name == “签到” 表示可签到，保存 scheme
- button.name 为 “已签/已签到/明日再来” 表示已签到

5) 执行签到
- scheme 形如 /api/container/button?...
- 访问 https://m.weibo.cn + scheme
- 返回 ok==1 且 msg 含“成功/签到”视为成功

核心代码（精简版）

import requests, json

HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "Referer": "https://m.weibo.cn/p/index?containerid=100803_-_followsuper",
}

def load_cookie_dict(path):
  with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
  return data["cookie_dict"]

def verify_login(session):
  r = session.get("https://m.weibo.cn/api/config", timeout=10)
  return r.status_code == 200 and r.json().get("data", {}).get("login") is True

def get_all_topics(session):
  url = "https://m.weibo.cn/api/container/getIndex"
  params = {
    "containerid": "100803_-_followsuper",
    "since_id": "{\"manage\":\"\",\"follow\":\"1022:1008081de9a5e2ea19a724e8917330088b5e16\",\"page\":1}"
  }
  cards = []
  while True:
    r = session.get(url, headers=HEADERS, params=params, timeout=10)
    data = r.json()
    if data.get("ok") != 1:
      break
    cards.extend(data["data"].get("cards", []))
    since_id = data["data"].get("cardlistInfo", {}).get("since_id")
    if not since_id:
      break
    params = {"containerid": "100803_-_followsuper", "since_id": since_id}
  return cards

def perform_checkin(session, scheme):
  if not scheme.startswith("/api/container/button"):
    return False
  url = "https://m.weibo.cn" + scheme
  r = session.get(url, headers=HEADERS, timeout=10)
  if r.status_code != 200:
    return False
  data = r.json()
  if data.get("ok") != 1:
    return False
  msg = (data.get("data") or {}).get("msg", "")
  return ("成功" in msg) or ("签到" in msg) or (msg == "")

def auto_checkin(cookie_path):
  session = requests.Session()
  session.cookies.update(load_cookie_dict(cookie_path))
  if not verify_login(session):
    return "cookie 失效"

  cards = get_all_topics(session)
  total = signed = success = failed = 0

  for card in cards:
    for item in card.get("card_group", []):
      if "title_sub" not in item or "buttons" not in item:
        continue
      total += 1
      buttons = item["buttons"]
      checkin_scheme = None
      for b in buttons:
        if b.get("name") == "签到":
          checkin_scheme = b.get("scheme")
          break
        if b.get("name") in ("已签", "已签到", "明日再来"):
          signed += 1
          checkin_scheme = None
          break
      if checkin_scheme:
        if perform_checkin(session, checkin_scheme):
          success += 1
        else:
          failed += 1

  return {"total": total, "signed": signed, "success": success, "failed": failed}