import io, csv, uuid, tempfile
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import  Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import Query, Delete
from database.Insert import Insert_Data
from database.Update import ReanalyzePosts
from tools.DataNormalizer import Normalizer
from tools.ExtractKeywords import ExtractKeywordsBatch
from tools.SentimentAnalysis import SentimentAnalysisBatch

posts_bp = Blueprint("posts", __name__, url_prefix='/posts')

# 上传文件的临时保存路径
UPLOAD_TMP_DIR = Path(tempfile.gettempdir()) / "app_uploads"
# 文件格式检查
ALLOWED_EXT = {'.csv'} 
def allowed_file_ext(name):
    return Path(name).suffix.lower() in ALLOWED_EXT

# 导入数据
@posts_bp.route('/import', methods=['POST'])
@jwt_required()
def import_posts():
    UPLOAD_TMP_DIR.mkdir(parents=True, exist_ok=True)
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'analyst' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    save_path = None
    try:
        # 暂存文件
        file = request.files.get('file')
        platform = request.form.get('platform')
        models = request.form.getlist('models[]')
        orig_name = secure_filename(file.filename)
        if not allowed_file_ext(orig_name):
            return jsonify({"message": "不允许的文件类型"}), 400
        unique_name = f"{uuid.uuid4().hex}_{orig_name}"
        save_path = UPLOAD_TMP_DIR / unique_name
        file.save(save_path)
    except Exception as e:
        return jsonify({"message": "读取文件时发生错误：" + str(e)}), 400
    try:
        # 数据标准化
        normalized_records = Normalizer(platform, str(save_path))
        contents = [r['content'] for r in normalized_records]
        # 关键词提取
        keywords_batch = ExtractKeywordsBatch(contents, top_n=10)
        # 情感分析
        sentiments_batch = SentimentAnalysisBatch(contents, models)
        # 合并结果 + 插入
        result = []
        for i, record in enumerate(normalized_records):
            record['keywords'] = keywords_batch[i]
            record['sentiments'] = sentiments_batch[i]
            result.append(record)
        Insert_Data(result)
    except Exception as e:
        return jsonify({"message": "处理数据时发生错误：" + str(e)}), 500
    finally:
        if save_path and save_path.exists():
            save_path.unlink()
    return jsonify({})

# 导出数据
@posts_bp.route('/export', methods=['GET'])
@jwt_required()
def export_posts():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'analyst' in roles and not 'ingest' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    topics_str = request.args.get('topics', '')
    keywords_str = request.args.get('keywords', '')
    platform = request.args.get('platform', '')
    model = request.args.get('model', '')
    type = request.args.get('type', '')
    keywords = keywords_str.split() if keywords_str else []
    topics = topics_str.split() if topics_str else []
    # 查询
    try:
        posts = Query.PostsWithSentiments(
            startTime=start_time, endTime=end_time,
            topics=topics, keywords=keywords,
            platform=platform, model=model, type=type
            )        
        if not posts:
            return jsonify({"message": "未查询到可导出的数据"}), 400
    except Exception as e:
        return jsonify({"message": "查询时发生错误：" + str(e)}), 500
    # 生成 csv 文件
    try:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            'post_id','platform','username',
            'location','create_time',
            'model','sentiment_type','score','analysis_time',
            'content'])
        for p in posts:
            if p.get('sentiments'):
                for s in p['sentiments']:
                    writer.writerow([
                        p.get('post_id'),
                        p.get('platform'),
                        p.get('username'),
                        p.get('location'),
                        p.get('create_time'),
                        s.get('model'),
                        s.get('type'),
                        s.get('score'),
                        s.get('analysis_time'),
                        p.get('content')
                    ])
            else:
                writer.writerow([
                    p.get('post_id'),
                    p.get('platform'),
                    p.get('username'),
                    p.get('location'),
                    p.get('create_time'),
                    '', '', '', '',
                    p.get('content')
                ])
        buf.seek(0)
    except Exception as e:
        return jsonify({"message": "生成文件时发生错误：" + str(e)}), 500
    return send_file(
        io.BytesIO(buf.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='export.csv'
    )

# 查询帖子
@posts_bp.route('/query', methods=['GET'])
@jwt_required()
def query_posts():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'analyst' in roles and not 'ingest' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    post_ids_str = request.args.get('post_ids', '')
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    topics_str = request.args.get('topics', '')
    keywords_str = request.args.get('keywords', '')
    platform = request.args.get('platform', '')
    model = request.args.get('model', '')
    type = request.args.get('type', '')
    post_ids = post_ids_str.split() if post_ids_str else []
    keywords = keywords_str.split() if keywords_str else []
    topics = topics_str.split() if topics_str else []
    # 查询
    try:
        posts = Query.PostsWithSentiments(
            post_ids = post_ids,
            startTime=start_time, endTime=end_time,
            topics=topics, keywords=keywords, 
            platform=platform, model=model, type=type
        )
    except Exception as e:
        return jsonify({"message": "查询时发生错误：" + str(e)}), 500
    # 传参
    for p in posts:
        if len(p['content']) > 255:
            p['content']  = p['content'][:252] + '...'
    return jsonify({"posts": posts})
    
# 删除帖子
@posts_bp.route('/delete', methods=['POST'])
@jwt_required()
def delete_posts():
    username = get_jwt_identity()
    if not 'analyst' in Query.SysUserRoles(username):
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    data = request.json
    post_ids = data.get('post_ids')
    deleted_ids = Query.Post_Ids(post_ids=post_ids)
    # 删除
    try:
        Delete.Posts(post_ids=post_ids)
    except Exception as e:
        return jsonify({"message": "删除时发生错误：" + str(e)}), 500
    return jsonify({"deleted_ids": deleted_ids})

# 删除情感分析记录
@posts_bp.route('/delete_sentiments', methods=['POST'])
@jwt_required()
def delete_sentiments():
    username = get_jwt_identity()
    if not 'analyst' in Query.SysUserRoles(username):
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    data = request.json
    post_ids = data.get('post_ids')
    model = data.get('model')
    # 删除
    try:
        Delete.Sentiments(post_ids=post_ids, models=[model])        
    except Exception as e:
        return jsonify({"message": "删除时发生错误：" + str(e)}), 500
    updated_posts = Query.PostsWithSentiments(post_ids=post_ids)
    for p in updated_posts:
        if len(p['content']) > 255:
            p['content']  = p['content'][:252] + '...'
    return jsonify({"updated_posts": updated_posts})

# 分析选中帖子
@posts_bp.route('/reanalyze', methods=['POST'])
@jwt_required()
def reanalyze_posts():
    username = get_jwt_identity()
    if not 'analyst' in Query.SysUserRoles(username):
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    data = request.json
    post_ids = data.get('post_ids')
    model = data.get('model')
    # 分析
    try:
        ReanalyzePosts(post_ids, model)
    except Exception as e:
        return jsonify({"message": "分析时发生错误：" + str(e)}), 500
    analyzed_posts = Query.PostsWithSentiments(post_ids=post_ids)
    for p in analyzed_posts:
        if len(p['content']) > 255:
            p['content']  = p['content'][:252] + '...'
    return jsonify({"analyzed_posts": analyzed_posts})