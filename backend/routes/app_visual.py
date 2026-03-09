import io
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from wordcloud import WordCloud

from database import Query
from tools.DataNormalizer import ToDate
from tools.GenerateHeatmap import GetLatLong, GenerateHeatmap

visual_bp = Blueprint("visual", __name__, url_prefix='/visual')

# 生成情感分布统计结果
@visual_bp.route('/sentiment_distribution', methods=['GET'])
@jwt_required()
def visual_sentiment_distribution():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'ingest' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    topics_str = request.args.get('topics', '')
    keywords_str = request.args.get('keywords', '')
    platform = request.args.get('platform', '')
    model = request.args.get('model', '')
    type = request.args.get('type', '') # 统计情感分布时，不使用 type 参数
    topics = topics_str.split() if topics_str else []
    keywords = keywords_str.split() if keywords_str else []
    # 查询情感类型分布
    try:
        typeCounts = Query.Sentiments_TypeCount(
            startTime=start_time, endTime=end_time,
            topics=topics, keywords=keywords,
            platform=platform, model=model,
            querySingleModel=True
        )
    except Exception as e:
        return jsonify({"message": "查询时发生错误：" + str(e)}), 500
    if not typeCounts:
        return jsonify({"message": "未查询到情感分析数据"}), 400
    counts = {tc['type']: tc['count'] for tc in typeCounts}
    return jsonify({'counts': counts})

# 生成情感时间趋势
@visual_bp.route('/sentiment_trend', methods=['GET'])
@jwt_required()
def visual_sentiment_trend():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'ingest' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    topics_str = request.args.get('topics', '')
    keywords_str = request.args.get('keywords', '')
    platform = request.args.get('platform', '')
    model = request.args.get('model', '')
    type = request.args.get('type', '')
    topics = topics_str.split() if topics_str else []
    keywords = keywords_str.split() if keywords_str else []
    # 查询
    try:
        timeTypeCounts = Query.Sentiments_TimeTypeCount(
            startTime=start_time, endTime=end_time,
            topics=topics, keywords=keywords, 
            platform=platform, model = model, type = type,
            querySingleModel=True
        )        
    except Exception as e:
        return jsonify({"message": "查询时发生错误：" + str(e)}), 500
    if not timeTypeCounts:
        return jsonify({"message": "未查询到情感分析数据"}), 400
    # 汇总数据
    trendData = {
        'dates': [], 
        'positive': [], 
        'neutral': [], 
        'negative': []
    }
    current_date = ToDate(timeTypeCounts[0]['create_time'])
    pos = neu = neg = 0
    for ttc in timeTypeCounts:
        date = ToDate(ttc['create_time'])
        if date != current_date:
            trendData['dates'].append(current_date)
            trendData['positive'].append(pos)
            trendData['neutral'].append(neu)
            trendData['negative'].append(neg)
            current_date = date
            pos = neu = neg = 0
        type = ttc['type']
        count = ttc['count']
        if type == 'positive':
            pos += count
        elif type == 'neutral':
            neu += count
        elif type == 'negative':
            neg += count
    trendData['dates'].append(current_date)
    trendData['positive'].append(pos)
    trendData['neutral'].append(neu)
    trendData['negative'].append(neg)
    return jsonify({'trendData': trendData})

# 生成关键词分布统计结果
@visual_bp.route('/top_words', methods=['GET'])
@jwt_required()
def visual_top_words():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'ingest' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    topics_str = request.args.get('topics', '')
    keywords_str = request.args.get('keywords', '')
    platform = request.args.get('platform', '')
    model = request.args.get('model', '')
    type = request.args.get('type', '')
    topics = topics_str.split() if topics_str else []
    keywords = keywords_str.split() if keywords_str else []
    max_words = int(request.args.get('max_words', 20))
    mode = request.args.get('mode', '')
    # 查询词分布
    try:
        wordCounts = Query.Words_Count(
            startTime=start_time, endTime=end_time,
            topics=topics, keywords=keywords, 
            platform=platform, model = model, type=type,
            mode=mode
        )
        if not wordCounts:
            return jsonify({"message": "未查询到词数据"}), 400
        match mode:
            case 'keywords':
                counts = [[wc['keyword'], wc['count']] for wc in wordCounts[:max_words]]
            case  'topics':
                counts = [[wc['topic'], wc['count']] for wc in wordCounts[:max_words]]
            case _:
                return jsonify({"message": "未知的处理类型"}), 401
    except Exception as e:
        return jsonify({"message": "查询时发生错误：" + str(e)}), 500
    return jsonify({'counts': counts})

# 生成关键词云
@visual_bp.route('/wordcloud', methods=['GET'])
@jwt_required()
def visual_wordcloud():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'ingest' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    topics_str = request.args.get('topics', '')
    keywords_str = request.args.get('keywords', '')
    platform = request.args.get('platform', '')
    model = request.args.get('model', '')
    type = request.args.get('type', '')
    topics = topics_str.split() if topics_str else []
    keywords = keywords_str.split() if keywords_str else []
    max_words = int(request.args.get('max_words', 20))
    mode = request.args.get('mode', '')
    # 查询词分布
    try:
        wordCounts = Query.Words_Count(
            startTime=start_time, endTime=end_time,
            topics=topics, keywords=keywords, 
            platform=platform, model = model, type=type,
            mode=mode
        )
        if not wordCounts:
            return jsonify({"message": "未查询到词数据"}), 400
        match mode:
            case 'keywords':
                counts = {wc['keyword']: wc['count'] for wc in wordCounts[:max_words]}
            case  'topics':
                counts = {wc['topic']: wc['count'] for wc in wordCounts[:max_words]}
            case _:
                return jsonify({"message": "未知的处理类型"}), 401
    except Exception as e:
        return jsonify({"message": "查询时发生错误：" + str(e)}), 500
    # 生成词云
    if len(counts)==0:
        img = WordCloud(width=800, height=400).generate("no data")
    else:
        img = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(counts)
    buf = io.BytesIO()
    img.to_image().save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png', download_name='wordcloud.png')

# 热力图
@visual_bp.route('/heatmap', methods=['GET'])
@jwt_required()
def visual_heatmap():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'ingest' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    topics_str = request.args.get('topics', '')
    keywords_str = request.args.get('keywords', '')
    platform = request.args.get('platform', '')
    model = request.args.get('model', '')
    type = request.args.get('type', '')
    topics = topics_str.split() if topics_str else []
    keywords = keywords_str.split() if keywords_str else []
    # 查询
    try:
        posts = Query.PostsWithSentiments(
            startTime=start_time, endTime=end_time,
            topics=topics, keywords=keywords, 
            platform=platform, model=model, type=type,
            querySingleModel=True
        )
    except Exception as e:
        return jsonify({"message": "查询时发生错误：" + str(e)}), 500
    # 地理位置转坐标，附上情感分析分数
    heatData = []
    for p in posts:
        lat, long = GetLatLong(p['location'])
        if lat and long:
            for s in p['sentiments']:
                heatData.append([lat, long, (float(s['score']) + 1) / 2])
    if not heatData:
        return jsonify({"message": "未查询到可绘制热力图的数据"}), 400
    # 生成热力图
    try:
        m = GenerateHeatmap(heatData)
    except Exception as e:
        return jsonify({"message": "生成热力图失败：" + str(e)}), 500
    # 将 folium 的 HTML 渲染成字符串
    html = m.get_root().render()
    buf = io.BytesIO()
    buf.write(html.encode('utf-8'))
    buf.seek(0)
    return send_file(buf, mimetype='text/html', download_name='heatmap.html')