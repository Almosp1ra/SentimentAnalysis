import re
import jieba
from janome.tokenizer import Tokenizer
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
import numpy as np

"""
关键词提取模块，使用 Tfidf 分词
"""

# 日文分词器
jp_tokenizer = Tokenizer()

# ---------------------------
# 停用词列表
# ---------------------------
cn_stopwords = set([
    "的", "了", "和", "是", "我", "也", "就", "在", "不", "有", "人", "都", "一个"
    # 可以自行扩充
])
jp_stopwords = set([
    "の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ"
])
en_stopwords = set(ENGLISH_STOP_WORDS)
en_stopwords.update(["https"])

# ---------------------------
# 语言检测，支持中/日/英
# ---------------------------
def detect_lang(text):
    if re.search(r'[\u3040-\u30ff\u31f0-\u31ff]', text):
        return "jp"
    elif re.search(r'[\u4e00-\u9fff]', text):
        return "cn"
    else:
        return "en"

# ---------------------------
# 中/日分词 + 去停用词
# ---------------------------
def tokenize(text):
    lang = detect_lang(text)
    if lang == "jp":
        tokens = [token.surface for token in jp_tokenizer.tokenize(text)]
        tokens = [t for t in tokens if t not in jp_stopwords]
    elif lang == "cn":
        tokens = list(jieba.cut(text))
        tokens = [t for t in tokens if t not in cn_stopwords]
    else:
        tokens = text.split()
        tokens = [t for t in tokens if t.lower() not in en_stopwords]
    return tokens

# ---------------------------
# 对外统一接口
# ---------------------------
def ExtractKeywords(text, top_n=5):
    tokens = tokenize(text)
    if not tokens:
        return []
    docs = [" ".join(tokens)]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(docs)
    scores = tfidf.toarray()[0]
    idxs = np.argsort(scores)[::-1][:top_n]
    feature_names = vectorizer.get_feature_names_out()
    keywords = [feature_names[i] for i in idxs]
    return keywords

# ---------------------------
# 批量关键词提取（优化版）
# ---------------------------
def ExtractKeywordsBatch(texts, top_n=5):
    if not texts:
        return [[] for _ in texts]  # 返回空列表列表，与输入长度匹配
    # 批量分词
    tokenized_texts = [tokenize(text) for text in texts if tokenize(text)]  # 过滤空文本
    if not tokenized_texts:
        return [[] for _ in texts]  # 所有文本为空，返回空列表
    # 合并所有文档为语料库
    corpus = [" ".join(tokens) for tokens in tokenized_texts if tokens]  # 确保非空
    if not corpus:
        return [[] for _ in texts]  # 语料库为空，返回空列表
    # 全局TF-IDF向量化（一次性fit所有文档）
    vectorizer = TfidfVectorizer(max_features=10000)  # 限制特征数以提高效率
    tfidf_matrix = vectorizer.fit_transform(corpus)  # 批量计算TF-IDF
    feature_names = vectorizer.get_feature_names_out()
    # 为每个文档提取关键词
    results = []
    for i, tokens in enumerate(tokenized_texts):
        if not tokens or i >= len(corpus):  # 处理空文本或索引越界
            results.append([])  # 空文本返回空关键词列表
            continue
        # 获取当前文档的TF-IDF分数（对应行）
        scores = tfidf_matrix[i].toarray()[0]  # 假设corpus顺序与tokenized_texts一致
        # 过滤出当前文档中存在的词（避免全局词汇表中的无关词）
        token_set = set(tokens)  # 当前文档的唯一词集合
        filtered_scores = [(feature_names[j], scores[j]) for j in range(len(feature_names)) if feature_names[j] in token_set and scores[j] > 0]  # 只考虑当前文档的词
        # 按分数排序，取前top_n
        filtered_scores.sort(key=lambda x: x[1], reverse=True)  # 降序排序
        keywords = [word for word, score in filtered_scores[:top_n]]  # 提取关键词
        results.append(keywords)  # 添加到结果列表
    # 处理原始texts中未分词的文本（如果有）
    while len(results) < len(texts):  # 填充空列表以匹配输入长度
        results.append([])  # 对于空文本，返回空关键词列表
    return results

# 测试程序
if __name__ == "__main__":
    # 英文测试
    text = """
        My storm finally and completely disappears. The last vestiges of the color I left in heaven die.

        But oh no, no, I am still here, Arcaea鈥攕till here.

        What an agonizingly long journey it has been.
        Yes... I am here now. I, who saw this place through a passing glance between realities and simply had to visit.

        I am thinking, even, of staying.

        You know, this world is broken now... but it's still here. That is beyond incredible. I have never seen
        something "shaped" this terribly and this greatly; I really need to dig into it鈥擨 need to know more
        about it. I need to learn about it, I need to find those who live their second lives here. In one case:
        a third! So, so incredible! And ah, what a lovely story of three lives!

        I run my hand through my hair as I think of it. Rainwater runs down over my skin, and I cannot help
        but laugh again. I hug myself, and soon find myself chuckling, and laughing, and laughing all the
        more until it almost hurts...!

        Because isn't it a shame? It's a shame, you know!? You see: this world has been missing a god! Ah, it had a
        god but for an instant! For a fleeting moment, it was whole and just after鈥攁h, it shattered at its very core!
        Have the people here been worried ever since?

        Oh, oh, there's no more need to worry. No, no, none have need of worry at all!

        This fading, sorrowful, wonderful world has been once again blessed...!

        In my grace, in my providence, you will all find happiness again...

        Yes... a god has come here to set everything right and well for you all.
"""

    # 日文测试
    text = """
        天国とは、地獄じごくの一種だ。

        結局のところ、情熱の天敵とは停滞ていたいした平和であり、思考の伴ともなわない喜びだ。
        摂取せっしゅという行為こうい自体と、無制限に幸福を伴うものの呑食どんじきは感覚を麻痺まひさせ、
        しまいには幸福自体を曖昧あいまいでぼやけたものにして、究極的には目的を見失わせる。

        だが今となっては、目的があるものなど一つもない。
        そもそも少女に目的なんてなかっただろうに。

        空の天蓋てんがいはもはや、目が潰つぶれそうなほどに眩い。


        少女はいま、放浪しているのか、立ち尽くしているのかもわからない。
        もはやどちらもよくわからないし、そもそも彼女にはどうでもよかった。
        編み上げた天蓋だけが、今の少女の唯一の関心事だった。
        だが、空に蠢うごめく記憶の群れにはもう、手の施しようがない。

        もはや不透明で膨大な濃霧のうむのようなそれは、どうしようもない空虚さをたたえている。
        彼女自身が既に、自分を見失いつつあった。

        自分自身を見失う傍かたわらで、少女はまだ迫り来る終焉に対して無自覚なままだった。
        自覚もないが、この心地よくも息苦しい飼育房を編み上げ、自身を幽閉ゆうへいしたのは少女自身だ。
        その脳裏には、とっくに憂うという意思すらなかった。


        空にきらめく天蓋がさらに輝くたび、少女は少女自身を喪うしなっていく。
        もはや幾許いくばくも残されていない時の中で、待ちわびるかのように虚空こくうを見上げている。

        明るく明らかに、至福で美しき天蓋。
        光ひかり輝く想おもい出でが、彼女を塗ぬり潰した。


        その精神は、焼き切れた。
        そして意味もなく、輝きは減衰していく。
        そして意義もなく、時間は過ぎていく。
        そうして未だに、少女その瞳は虚無の天蓋を映している。

        ……こうして、彼女の心は、物語おもいでと共に終わった。
    """
    keywords = ExtractKeywords(text, 10)
    print(keywords) 

    # 中文测试
    text = """
        结局。

        被阴影纠缠的少女，目光穿过那扇破碎的窗户，投射到另一段时光之中。
        微笑，回到了她的脸上。

        她可真是个无可救药的傻子。
        不，不是那白衣少女。
        是她自己。

        那片玻璃中的影像并不是回忆。

        当然，这并不现实。
        她所看见的是未来——那个她理应期待万分的未来，
        那个白痴，愚蠢的梦想家。

        那些玻璃毫无偏差地映照出了她自己的身体被一根参差的玻璃长柱一穿而过的影像。
        那道创伤仿佛要在炙热，苍白的烈焰中将她的衣服与整个身躯撕裂。

        空虚荒芜的Arcaea大地，从她的身前和身后延伸到无边无际的地平线。
        带着缠绕双肩的那两股刺眼的炙热火焰，抬起手轻抚着长柱的，
        是那位身披白衣，使她倍感熟悉的少女——尽管在这个角度看不到她的表情。

        她，是此时此刻正站在自己面前的少女。
        那名才与她相遇不久的女孩。
        这绝不是回忆：这景象预言着未来将会发生的一切。

        面对此景，对立退回了自己的立场，
        并对峙起那段她原先计划彻底无视的真相。

        她已无所谓自己有没有心怀信念。
        她已不会在这世界中找到任何对她有利的事物。

        最后一丝希望也终被墨染，淹没在绝望之中，最终被彻底遗忘。

        还有什么事会发生？
        她还期望着什么？
        愚蠢。令人厌烦。盲目的愚蠢。

        令人厌烦的努力。
        令人厌烦的回忆。
        令人厌烦的存在。

        令人厌烦，糟糕得不可理喻——使她作呕。对这一切感到作呕，对她自己感到作呕，
        对这永无止境的嘲讽游戏中所存在的一切事物感到作呕。

        奇迹？别开玩笑了……

        她早已对自己说过。这个世界是地狱。
        她是从种种显示这世界已经死透了的事物得知的：
        在这世界之中，即便天使也终会堕落，而后苏醒为恶魔。

        在光芒中的少女就是这样。
        在这被诅咒的终末展开中，就算是她心中原先微不足道的小洞也被残暴地刨开，并迅速扩大——
        荒废，并在刹那间彻底腐朽，只留下一道冰冷的无底深渊。

        正当蕴藏其中的黑暗席卷并吞噬少女，尝试扼杀她的思绪之时，
        她清晰地看见了光。

        她看见光的视线投向那片碎片——捕捉到她眼中存在的恐慌与那明澈的认知。

        这女孩已经知道了。
        而现在，她已无法直视来自对面的视线。
        一言不发，哪怕一切尽在眼底。

        你此刻感到紧张吗？是否心情不安？毫不掩饰。
        不可原谅。

        那股愤怒扭曲成厌恶与憎恨，如同滚滚黑云般显现于她的双眼之中。

        邪恶的背叛者；邪恶，邪恶的地方。
        她紧紧抓着她的阳伞，
        越过碎片注视着伫立于原地的光。

        仿佛冻结在原地——当然，因为她病态的意图已经被识破了。
        这可真是令人发笑。

        对立的双眼微闭。
        她抹除了那女孩尝试在她心中种下的一切情感之芽。

        结局到来的那一刻，她的心智终于被掏空了。
        而这一刻起，她终于弄清自己应该做些什么。

        只是，这是面单向的镜子——其中蕴藏的厌恶与冷淡也是相同。
        光对这片不同寻常的碎片之中所蕴含的内容完全无从知晓。

        当对立的脸上失去越来越多的血色，
        丝毫未意识到情势的走向——光仅能在困惑中观察着一切。

        一股突如其来的危机感扩散至身体的每一个角落。尽管她并不理解原由，她却能感受到危机就在眼前。
        事实上，匍匐于大地的暗影如今已翻腾而起，毁灭着它所接触的一切光芒。

        黑暗向着她逼近，而她的呼吸变得愈发急促。她不禁朝着后方退了一步。
        她几乎无法相信眼前正在发生的事情。她根本不想去相信。

        即使她已于那片耀眼的天空所带来的痛苦折磨中幸存下来，
        某种可怕的事物再次毫无理由地显现于她的面前。

        尽管，她仍旧存活了下来。
        而她终究意识到，生存并不是件能够妥协的事情。

        心中怀着这样的想法，光犯下了一个天大的错误。

        她伸手去拿了那片玻璃——
        那片在她彻底迷失于低谷时，给予她慰藉与方向的玻璃。

        就在她将它提至胸前时，
        对立头颈后方的头发也飞扬起来。

        恐惧猛烈地冲击着她的全身。伴随着那永远不愿再次遭遇不幸的决意，
        那一刹那，对立在没有任何预警的情况下靠近了光，
        准备彻底夺走她的性命。
    """
    keywords = ExtractKeywords(text, 10)
    print(keywords)  