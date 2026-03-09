from textblob import Blobber
from tools.Translation import baidu_translate
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import numpy as np, math, datetime
from langdetect import detect

"""
情感分析模块，提供 TextBlob + 翻译 API 和 BERT 两种分析模型的选择
对外提供数据批量分析的接口，可通过传输列表参数选择多个模型 
"""

tb = Blobber()

# ---------------------------
# 工具函数
# ---------------------------
def Score2Type(score):
    if score > 0.2:
        return 'positive'
    if score < -0.2:
        return 'negative'
    return 'neutral'

def NeedTranslate(text, target_lang='en'):
    try:
        lang = detect(text)
    except:
        return True
    return lang != target_lang

# ---------------------------
# TextBlob
# ---------------------------
def TextBlob_Sentiment(text):
    if NeedTranslate(text):
        try:
            text = baidu_translate(text)
        except Exception as e:
            print(f"翻译出错，直接使用原文本进行分析：{e}")
            pass
    sentiment = tb(text).sentiment
    return sentiment.polarity * math.sqrt(sentiment.subjectivity)

# ---------------------------
# BERT
# ---------------------------
model_path = "D:/NewFiles/pythonSaves/database/Project/backend/models/BERT"
#model_path = "../models/BERT"
model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
try:
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
except Exception as e:
    print("BERT 本地缓存加载失败，尝试从 Hugging Face 下载:", e)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

sentiment_analyzer = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

def BERT_ToPolarity(output):
    star = int(output['label'].split()[0])
    polarity = (star - 3) / 2 * output['score']
    return polarity

def BERT_Sentiment(text):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()] or [text.strip()]
    outputs = sentiment_analyzer(paragraphs, truncation=True, max_length=512)
    polarities, weights = [], []
    for output in outputs:
        polarities.append(BERT_ToPolarity(output))
        weights.append(output['score'])
    return np.average(polarities, weights=weights)

# ---------------------------
# 对外接口，modelList：'textblob', 'bert'
# ---------------------------

# 情感分析
def SentimentAnalysis(text, modelList=[]):
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result = []
    for model in modelList or []:
        sentiment = {}
        if model == 'textblob':
            sentiment['score'] = TextBlob_Sentiment(text)
        elif model == 'bert':
            sentiment['score'] = BERT_Sentiment(text)
        else:
            continue
        sentiment['type'] = Score2Type(sentiment['score'])
        sentiment['model'] = model
        sentiment['analysis_time'] = time
        result.append(sentiment)
    return result

# 情感分析批处理
def SentimentAnalysisBatch(texts, modelList=[]):
    results = []
    for text in texts:
        results.append(SentimentAnalysis(text, modelList))
    return results

# 测试程序
if __name__ == "__main__":
    text = """
        Her first impression was that she'd awakened to a cloud of glass butterflies.
        "How pleasant," she thought, "that these figures can move as well. Where are the strings?"

        She sat onto her knees, fixed her dress, and found that there were no strings, and these were not
        butterflies. Glass shards, flying on their own. "Delightful!" she felt, and so she said it.

        The glass reflected another world than the one in white surrounding her. In it she could see
        reflections of seas, cities, fires, lights; she rose her hand to scatter them, and laughed in joy.

        She didn't know these pieces of glass had a name: Arcaea.
        To tell the truth, they were so beautiful that it didn't matter the name.
        She entertained herself by touching them, swirling them, watching them.
        That was enough, no?

        There were six questions to ask: who, what, where, when, why, and how.
        Of these questions, she asked none and desired no answers,
        content instead to bask in the glow of Arcaea.
        This was her meeting with a new world.
    """
    for s in SentimentAnalysis(text, ['bert']):
        print(s)

    text = """
        マヤ……そうだよ。そうさ、全てはキミに会うために。
        
    """
    for s in SentimentAnalysis(text, ['bert']):
        print(s)

    text = """
        宛如受石油污染的海洋，那受诅咒的迷宫记忆，与少女吸引而来的回忆碎片一齐摔落下来，
        与那些抚慰着她的碎片纠缠在了一起。
    """
    for s in SentimentAnalysis(text, ['bert']):
        print(s)