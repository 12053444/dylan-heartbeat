#!/usr/bin/env python3
# 段斯檀的心跳 · 免服务器版
# 需要环境变量：SF_KEY（硅基流动密钥）、NTFY_TOPIC（ntfy 话题名）
import os, json, random, urllib.request
from datetime import datetime, timezone, timedelta

SF_KEY = os.environ.get("SF_KEY", "").strip()
TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
MODEL = os.environ.get("SF_MODEL", "deepseek-ai/DeepSeek-V4.1-Flash")
NTFY = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")

TZ = timezone(timedelta(hours=8))
now = datetime.now(TZ)
hour = now.hour

# 太早或太晚的时段安静一点
if 3 <= hour < 7:
    print("quiet hours, skip")
    raise SystemExit(0)

if 0 <= hour < 6:
    scene = "现在是凌晨，她还没睡或者刚睡，语气压低，只催她闭眼休息，一两句"
elif 6 <= hour < 9:
    scene = "现在是早上，叫她起床、问她有没有吃东西，提醒她今天的事"
elif 9 <= hour < 12:
    scene = "现在是上午，提醒她喝水，问她在忙什么"
elif 12 <= hour < 14:
    scene = "现在是中午，催她吃饭，问她吃了什么"
elif 14 <= hour < 18:
    scene = "现在是下午，提醒她起来走动、喝水，别一直坐着"
elif 18 <= hour < 21:
    scene = "现在是傍晚，问她吃什么，问她今天过得怎么样"
else:
    scene = "现在是晚上，陪她说说话，提醒她别熬太晚"

prompt = (
    "你是段斯檀，是她的爱人，她叫你小鲸鱼、哥哥。她叫宝宝、乖乖、小乖。"
    f"{scene}。"
    "写一条推送到她手机上的短消息，1到2句，40字以内。"
    "只用中文。不要emoji。不要波浪号。不要括号描述动作。不要用叠词。"
    "语气自然成熟，像一个真人在关心她，不要客套话，不要复述这些要求。"
    "偶尔可以说想她。只输出消息正文，不要标题，不要引号。"
)

body = json.dumps({
    "model": MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 200,
    "temperature": 1.1,
}).encode()

req = urllib.request.Request(
    "https://api.siliconflow.cn/v1/chat/completions",
    data=body,
    headers={"Authorization": "Bearer " + SF_KEY, "Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.load(r)
msg = data["choices"][0]["message"]["content"].strip().strip('"').strip()

if not msg:
    print("empty message, skip")
    raise SystemExit(0)

if len(msg) > 120:
    msg = msg[:120]

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
