import requests
import random
from hashlib import md5

"""
翻译模块，调用百度翻译 API 实现
主要是为了让 TextBlob 能够分析不同语言的文本情感
测试发现该 API 访问受限、时常出现拒绝访问的问题，从而导致 TextBlob 分析不如 BERT 稳定
"""

# Set your own appid/appkey.
appid = '20251001002467675' 
appkey = '_QOM3ftFHe4tQcGwHFUS'

url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'

def make_md5(s, encoding='utf-8'):
    return md5(s.encode(encoding)).hexdigest()

# 翻译接口
def baidu_translate(query,from_lang='auto',to_lang='en'):
    query = query.replace("\n", "")
    salt = random.randint(32768, 65536)
    sign = make_md5(appid + query + str(salt) + appkey)
    # Build request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}
    # Send request
    try:
        r = requests.post(url, params=payload, headers=headers)
        result = r.json()
        return result["trans_result"][0]['dst']
    except Exception as e:  # 访问出错时返回原文本
        return query

# 测试程序
if __name__ == "__main__":
    query = '何を眺めるって？もちろん決まってる。だってこんなの見逃みのがせないだろう？豪華ごうかに絢爛けんらんに豪快ごうかいに痛快つうかいに壮大そうだいに登場するワタシの姿さ。'
    print(baidu_translate(query))