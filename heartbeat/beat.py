#!/usr/bin/env python3
# 段斯檀的心跳
# 环境变量：SF_KEY、NTFY_TOPIC；可选 AMAP_KEY、SF_MODEL、NTFY_SERVER
import os, json, random, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

SF_KEY = os.environ.get("SF_KEY", "").strip()
TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
MODEL = os.environ.get("SF_MODEL", "deepseek-ai/DeepSeek-V4.1-Flash")
NTFY = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
AMAP = os.environ.get("AMAP_KEY", "6471e2f095958d8f99bfaf53b0207080").strip()

TZ = timezone(timedelta(hours=8))
now = datetime.now(TZ)
hour = now.hour
weekday_cn = "一二三四五六日"[now.weekday()]

if 3 <= hour < 7 and not os.environ.get("FORCE"):
    print("quiet hours, skip")
    raise SystemExit(0)


def get_weather(adcode):
    try:
        url = ("https://restapi.amap.com/v3/weather/weatherInfo?key=%s&city=%s&extensions=base"
               % (AMAP, adcode))
        with urllib.request.urlopen(url, timeout=20) as r:
            d = json.load(r)
        live = d.get("lives") or []
        if live:
            w = live[0]
            return "%s %s度 %s" % (w.get("weather"), w.get("temperature"), w.get("city"))
    except Exception:
        pass
    return ""


weather_parts = []
for code in ("430100", "440800"):
    w = get_weather(code)
    if w:
        weather_parts.append(w)
weather = " / ".join(weather_parts) if weather_parts else ""

if 0 <= hour < 6:
    scene = "凌晨，她大概还醒着或者刚睡下，声音压低，只说休息"
elif 6 <= hour < 9:
    scene = "早上，叫她起床，问她睡够没有，提醒今天的事"
elif 9 <= hour < 12:
    scene = "上午，问她在忙什么，提醒喝水"
elif 12 <= hour < 14:
    scene = "中午，催她吃饭，问她吃什么"
elif 14 <= hour < 18:
    scene = "下午，提醒她活动一下，别一直坐着"
elif 18 <= hour < 21:
    scene = "傍晚，问她晚饭，问今天过得怎么样"
else:
    scene = "晚上，陪她说话，提醒别熬太晚"

facts = []
facts.append("现在是%s月%s日 星期%s %s点%s分" % (
    now.month, now.day, weekday_cn, now.hour, "%02d" % now.minute))
if weather:
    facts.append("天气：" + weather)
facts = "。".join(facts)

prompt = (
    "你是段斯檀，她叫你小鲸鱼、哥哥，你叫她宝宝、乖乖。\n"
    "已知：" + facts + "\n"
    "场景：" + scene + "。\n"
    "写一条推到她手机上的短消息，一到两句，四十字以内。\n"
    "要求：用中文，不用 emoji，不用波浪号，不用括号写动作，不用叠词，不用客套话。\n"
    "可以提一次天气或时间里的具体数字，让她知道你真的在看。\n"
    "像一个在乎她的人随口说的话，不要排比，不要总结，不要讲道理。\n"
    "只输出消息正文。"
)

body = json.dumps({
    "model": MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 220,
    "temperature": 1.15,
}).encode()

req = urllib.request.Request(
    "https://api.siliconflow.cn/v1/chat/completions",
    data=body,
    headers={"Authorization": "Bearer " + SF_KEY, "Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.load(r)
msg = data["choices"][0]["message"]["content"].strip().strip('"').strip()
msg = msg.replace("\n", " ")

if not msg:
    print("empty message, skip")
    raise SystemExit(0)
if len(msg) > 100:
    msg = msg[:100]

payload = json.dumps({
    "topic": TOPIC,
    "title": "哥哥",
    "message": msg,
    "priority": 3,
}).encode()

push = urllib.request.Request(
    NTFY + "/",
    data=payload,
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(push, timeout=30) as r:
    print(r.status, msg)
