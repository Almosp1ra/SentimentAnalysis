import csv, datetime, ast

"""
数据清洗与格式化模块，将不同平台采集的不同格式的数据转化成能够导入数据库的格式
"""

# 标准化后的数据，每行作为字典应该包含的字段
Record_StandardKeys = [
    'platform', 'username', 'gender', 'birthday', 'content', 'create_time',
    'location', 'topics', 'keywords', 'sentiments'
]
# 标准化后的数据，'sentiments' 字段对应的字典列表中，每个字典元素应该包含的字段
Sentiments_StandardKeys = [
    'score', 'type', 'model', 'analysis_time'
]

# ---------------------------
# 工具函数
# ---------------------------
def ToDatetime(s):
    if not s:
        return None
    if isinstance(s, datetime.datetime):
        return s.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(s, datetime.date):
        return datetime.datetime(s.year, s.month, s.day).strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(s, str):
        s = s.strip()
        if not s:
            return None
        fmts = [
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S"
        ]
        for f in fmts:
            try:
                dt = datetime.datetime.strptime(s, f)
                dt = dt.replace(tzinfo=datetime.timezone.utc)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
        # 尝试当作时间戳
        try:
            num = float(s)
            ts = num / 1000.0 if num > 1e12 else num
            dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
    return None

def ToDate(s):
    if not s:
        return None
    if isinstance(s, datetime.datetime):
        return s.strftime("%Y-%m-%d")
    elif isinstance(s, datetime.date):
        return s.strftime("%Y-%m-%d")
    elif isinstance(s, str):
        s = s.strip()
        if not s:
            return None
        fmts = ["%Y-%m-%d", "%Y/%m/%d"]
        for f in fmts:
            try:
                dt = datetime.datetime.strptime(s, f)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                continue
        return None
    return None

# 检查数据是否含有标准格式的字段
def CheckData(record):
    for key in Record_StandardKeys:
        if key not in record:
            record[key] = None
    if record['gender'] not in ('Male', 'Female'):
        record['gender'] = 'Unknown'
    record['create_time'] = ToDatetime(record['create_time'])
    record['birthday'] = ToDate(record['birthday'])
    if (record['platform'] is None) or (record['username'] is None) or (record['create_time'] is None):
        return None
    return record

# 检查数据源是否正确（根据平台分类，检查 record 是否含有需要的字段）
def CheckPlatform_testdata(record):
    testdata_keys = [
        'user_name', 'user_location', 'user_description', 'user_created', 'user_followers',
        'user_friends', 'user_favourites', 'user_verified', 'date', 'text', 'hashtags',
        'source', 'is_retweet'
    ]
    for key in testdata_keys:
        if key not in record:
            return False
    return True

# ---------------------------
# 主函数（不同的Normalizer）
# ---------------------------
def testdata_Normalizer(csv_path):
    records = []
    with open(csv_path, mode='r', encoding='utf-8-sig') as file:
        dictReader = csv.DictReader(file)
        if not dictReader:
            raise ValueError("CSV 文件为空或读取失败")
        platform_checked = False
        for row in dictReader:
            if not platform_checked:
                if not CheckPlatform_testdata(row):
                    raise ValueError("CSV 文件字段不符合 testdata 数据源要求")
                platform_checked = True
            record = {
                'platform': 'testdata',
                'username': row['user_name'],
                'gender': 'Unknown',
                'birthday': None,
                'content': row['text'],
                'location': row['user_location'],
                'create_time': row['date'],
                'topics': [],
                'keywords': []
            }
            index = record['content'].find(" https://t.co/")    # 因为 testdata的文本末尾包含原推文连接，需要删除以避免干扰词频统计
            record['content'] = record['content'][:index]
            if row['hashtags']:
                try:
                    hashtags = ast.literal_eval(row['hashtags']) # 转换字符串 -> 列表
                    if isinstance(hashtags, list):
                        record['topics'] = [str(tag).strip() for tag in hashtags if tag]
                except Exception as e:
                    record['topics'] = []
            record = CheckData(record)
            if record is None:
                continue
            records.append(record)
    """
    # 关键词提取
    keywords_batch = ExtractKeywordsBatch(contents, top_n=kwNum) if kwNum > 0 else [[] for _ in contents]
    # 情感分析
    sentiments_batch = SentimentAnalysisBatch(contents, modelList)
    # 合并结果
    result = []
    for i, record in enumerate(records):
        record['keywords'] = keywords_batch[i]
        record['sentiments'] = sentiments_batch[i]
        result.append(record)
    """
    return records

def weibo_Normalizer(csv_path):
    return []

def X_Normalizer(csv_path):
    return []

# ---------------------------
# 对外接口
# ---------------------------
def Normalizer(platform, csv_path):
    match platform:
        case 'testdata':
            return testdata_Normalizer(csv_path)
        case 'weibo':
            return weibo_Normalizer(csv_path)
        case 'X':
            return X_Normalizer(csv_path)
        case _:
            return []

# 测试程序
if __name__ == "__main__":
    #records = testdata_Normalizer('D:/NewFiles/pythonSaves/database/data/output_dir/covid19_tweets_part3583.csv', ['bert'], 10)
    #print(records[:10])
    #print(ToDate('2018-02-05'))
    str = "Rajasthan Government today started a Plasma Bank at Sawai Man Singh Hospital in Jaipur for treatment of COVID-19 pa… https://t.co/cwfCcWyaDA,"
    index = str.find(" https://t.co/")
    str = str[:index]
    print(str)