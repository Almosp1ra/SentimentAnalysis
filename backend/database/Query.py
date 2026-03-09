from database.DbConnection import ConnectDatabase
from tools.DataNormalizer import ToDate
import datetime

# ---------------------------
# 查询执行函数
# ---------------------------
def Query(sql, params, fetch_mode='all'):
    conn = ConnectDatabase()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    if fetch_mode == 'one':
        data = cursor.fetchone()
    else:
        data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# ---------------------------
# 工具函数
# ---------------------------

# 处理参数，返回where语句列表、参数列表和join语句
def HandlePostQueryParams(
        post_ids=None, 
        startTime='', endTime='',
        topics=None, keywords=None,
        platform='', model='', type=''
    ):
    # 参数处理
    if startTime:
        startTime = ToDate(startTime)
    if endTime:
        end_dt = datetime.datetime.strptime(ToDate(endTime), "%Y-%m-%d")
        endTime = (end_dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    # sql 语句生成
    where_clauses = []
    params = []
    # post_ids
    if post_ids:
        where_clauses.append(f"posts.post_id IN ({",".join(["%s"] * len(post_ids))})")
        params.extend(post_ids)
    # 时间
    if startTime and endTime:
        where_clauses.append("posts.create_time BETWEEN %s AND %s") 
        params.extend([startTime, endTime])
    elif startTime:
        where_clauses.append("posts.create_time >= %s") 
        params.extend([startTime])
    elif endTime:
        where_clauses.append("posts.create_time <= %s") 
        params.extend([endTime])
    # 社交媒体平台
    if platform: 
        where_clauses.append("users.platform = %s")
        params.append(platform)
    # 情感分析模型
    if model:
        if model != 'none':
            where_clauses.append("sentiments.model = %s")    
            params.append(model)
        else:
            where_clauses.append("sentiments.post_id IS NULL")
    # 情感类型
    if type:   
        where_clauses.append("sentiments.type = %s")
        params.append(type)
    # topics
    if topics:
        topic_clause = f"""
            EXISTS (
                SELECT 1 FROM posts_topics AS pt
                JOIN topics AS t ON pt.topic_id = t.topic_id
                WHERE pt.post_id = posts.post_id
                AND ({' OR '.join(["t.topic LIKE %s"] * len(topics))})
            )
        """
        where_clauses.append(topic_clause)
        params.extend(['%' + t + '%' for t in topics])
    # keywords
    if keywords:
        keyword_clause = f"""
            EXISTS (
                SELECT 1 FROM posts_keywords AS pk
                JOIN keywords AS k ON pk.keyword_id = k.keyword_id
                WHERE pk.post_id = posts.post_id
                AND ({' OR '.join(["k.keyword LIKE %s"] * len(keywords))})
            )
        """
        where_clauses.append(keyword_clause)
        params.extend(['%' + k + '%' for k in keywords])
    # joins
    joins = ""
    if platform: 
        joins += " JOIN users ON posts.user_id = users.user_id "
    if model or type: 
        joins += " LEFT JOIN sentiments ON posts.post_id = sentiments.post_id "
    return where_clauses, params, joins


# ---------------------------
# 对外接口
# ---------------------------

# 查询帖子 id，直接返回 id 列表
def Post_Ids(
        post_ids=None, 
        startTime='', endTime='',
        topics=None, keywords=None,
        platform='', model='', type=''
    ):
    # sql 语句生成
    where_clauses, params, joins = HandlePostQueryParams(
        post_ids=post_ids, 
        startTime=startTime, endTime=endTime,
        topics=topics, keywords=keywords,
        platform=platform, model=model, type=type
    )
    # 拼接 SQL, 查询符合的post_id
    sql = f"""
        SELECT posts.post_id
        FROM posts
        {joins}
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
    """
    # 查询
    rows = Query(sql, tuple(params))
    return [r['post_id'] for r in rows or []]

# 查询帖子和情感分析记录
def PostsWithSentiments(
        post_ids=None, 
        startTime='', endTime='',
        topics=None, keywords=None,
        platform='', model='', type='',
        querySingleModel=False
    ):
    # 查询符合的 post_id
    pids = Post_Ids(
        post_ids=post_ids, 
        startTime=startTime, endTime=endTime,
        topics=topics, keywords=keywords,
        platform=platform, model=model, type=type
    )
    if not pids:
        return []
    # 拼接 SQL, 通过 pid 查询多种信息
    params = pids
    sql = f"""
        SELECT posts.post_id, users.platform, users.username,
            posts.location, posts.content, posts.create_time,
            sentiments.score, sentiments.type, sentiments.model, sentiments.analysis_time
        FROM posts JOIN users ON posts.user_id = users.user_id
        LEFT JOIN sentiments ON posts.post_id = sentiments.post_id
        WHERE posts.post_id IN ({','.join(["%s"] * len(pids))})
    """
    if querySingleModel and model and model != 'none':    # 只查询一个指定模型的情感记录，而不是查询被该模型分析的帖子的所有情感记录
        sql += " AND sentiments.model = %s"
        params.append(model)
    # 查询
    rows = Query(sql, tuple(params))
    # 合并相同帖子的不同情感分析记录
    posts_with_sentiments = {}
    for r in rows:
        post_id = r['post_id']
        if post_id not in posts_with_sentiments:
            posts_with_sentiments[post_id] = {
                'post_id': r['post_id'],
                'platform': r['platform'],
                'username': r['username'],
                'location': r['location'],
                'content': r['content'],
                'create_time': r['create_time'],
                'sentiments': []
            }
        if r['model']:
            posts_with_sentiments[post_id]['sentiments'].append({
                'score': r['score'],
                'type': r['type'],
                'model': r['model'],
                'analysis_time': r['analysis_time']
            })
    return list(posts_with_sentiments.values())

# 仅通过 id 查询帖子，返回 id 和 content 列表
def Post_Contents(post_ids=None):
    # 查询符合的 post_id
    pids = Post_Ids(post_ids=post_ids)
    if not pids:
        return []
    # 拼接 SQL
    sql = f"""
        SELECT posts.post_id, posts.content
        FROM posts
        WHERE posts.post_id IN ({','.join(["%s"] * len(pids))})
    """
    # 查询
    return Query(sql, tuple(pids))

# 查询情感类型分布
def Sentiments_TypeCount(
        startTime='', endTime='',
        model='', platform='',
        topics=None, keywords=None,
        querySingleModel=False
    ):
    # 查询符合的 post_id
    pids = Post_Ids(
        startTime=startTime, endTime=endTime,
        topics=topics, keywords=keywords,
        platform=platform, model=model
    )
    if not pids:
        return []
    # 拼接 SQL
    sql = f"""
        SELECT type, COUNT(*) AS count
        FROM posts
        JOIN sentiments ON posts.post_id = sentiments.post_id
        WHERE posts.post_id IN ({','.join(["%s"] * len(pids))})
    """
    params = pids
    if querySingleModel and model and model != 'none':    # 只查询一个指定模型的情感记录，而不是查询被该模型分析的帖子的所有情感记录
        sql += " AND sentiments.model = %s"
        params.append(model)
    sql += """
        GROUP BY type
    """
    # 查询
    return Query(sql, tuple(params))

# 查询情感类型随时间的分布
def Sentiments_TimeTypeCount(
        startTime='', endTime='',
        model='', platform='',
        topics=None, keywords=None, type='',
        querySingleModel=False
    ):
    # 查询符合的 post_id
    pids = Post_Ids(
        startTime=startTime, endTime=endTime,
        topics=topics, keywords=keywords,
        platform=platform, model=model, type=type
    )
    if not pids:
        return []
    # 拼接 SQL
    sql = f"""
        SELECT create_time, type, COUNT(*) AS count
        FROM posts
        JOIN sentiments ON posts.post_id = sentiments.post_id
        WHERE posts.post_id IN ({','.join(["%s"] * len(pids))})
    """
    params = pids
    if querySingleModel and model and model != 'none':    # 只查询一个指定模型的情感记录，而不是查询被该模型分析的帖子的所有情感记录
        sql += " AND sentiments.model = %s"
        params.append(model)
    sql += """
        GROUP BY create_time, type
        ORDER BY create_time ASC
    """
    # 查询
    return Query(sql, tuple(params))

# 查询关键词/话题分布
def Words_Count(
        startTime='', endTime='',
        model='', platform='',
        topics=None, keywords=None, type='',
        mode='keywords'
    ):
    if mode != 'keywords' and mode != 'topics':
        return []
    # 查询符合的 post_id
    pids = Post_Ids(
        startTime=startTime, endTime=endTime,
        topics=topics, keywords=keywords,
        platform=platform, model=model, type=type
    )
    if not pids:
        return []
    # 拼接 SQL，查询 keywords 或 topics
    if mode == 'keywords':
        sql = f"""
            SELECT keyword, COUNT(*) AS count
            FROM posts
            JOIN posts_keywords AS pk ON posts.post_id = pk.post_id
            JOIN keywords AS k ON pk.keyword_id = k.keyword_id
            WHERE posts.post_id IN ({",".join(["%s"] * len(pids))})
            GROUP BY keyword
            ORDER BY count DESC
        """
    elif mode == 'topics':
        sql = f"""
            SELECT topic, COUNT(*) AS count
            FROM posts
            JOIN posts_topics AS pt ON posts.post_id = pt.post_id
            JOIN topics AS t ON pt.topic_id = t.topic_id
            WHERE posts.post_id IN ({",".join(["%s"] * len(pids))})
            GROUP BY topic
            ORDER BY count DESC
        """
    # 查询
    return Query(sql, tuple(pids))

# 查询系统用户和其拥有的角色
def SysUsersWithRoles(user_ids=None, usernames=None):
    # sql 语句生成
    where_clauses = []
    params = []
    # user_ids
    if user_ids:
        where_clauses.append(f"u.user_id IN ({",".join(["%s"] * len(user_ids))})")
        params.extend(user_ids)
    # 用户名
    if usernames:
        where_clauses.append('(' + ' OR '.join([f"u.username LIKE %s" ] * len(usernames)) + ')')
        params.extend(['%' + n + '%' for n in usernames])
    # 拼接 SQL
    sql = f"""
        SELECT u.user_id, u.username, u.is_active,
            r.name
        FROM sys_users AS u
        LEFT JOIN sys_users_roles AS ur ON u.user_id = ur.user_id
        LEFT JOIN sys_roles  AS r ON r.role_id = ur.role_id
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
    """
    # 查询
    rows = Query(sql, tuple(params))
    # 合并相同用户的不同角色
    users_with_roles = {}
    for r in rows:
        user_id = r['user_id']
        if user_id not in users_with_roles:
            users_with_roles[user_id] = {
                'user_id': r['user_id'],
                'username': r['username'],
                'is_active': r['is_active'],
                'roles': []
            }
        if r['name']:
            users_with_roles[user_id]['roles'].append(r['name'])
    return list(users_with_roles.values())

# 仅通过 id 查询用户，返回 id 列表
def User_Ids(user_ids=None):
    # sql 语句生成
    where_clauses = []
    params = []
    joins = ""
    # user_ids
    if user_ids:
        where_clauses.append(f"users.user_id IN ({",".join(["%s"] * len(user_ids))})")
        params.extend(user_ids)
    # 拼接 SQL
    sql = f"""
        SELECT users.user_id
        FROM users
        {joins}
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
    """
    # 查询
    return Query(sql, tuple(params))

# 查询系统用户
def SysUser(username):
    sql = """
        SELECT u.user_id, u.username, u.password_hash, u.is_active
        FROM sys_users AS u
        WHERE username = %s
    """
    # 查询
    return Query(sql, (username,), fetch_mode='one')

# 查询角色
def SysRoles(role_names=None):
    sql = f"""
        SELECT r.role_id, r.name
        FROM sys_roles AS r
    """ + (f"WHERE name IN ({",".join(["%s"] * len(role_names))})" if role_names else '')
    # 查询
    return Query(sql, tuple(role_names) if role_names else None)

# 查询指定用户的角色
def SysUserRoles(username):
    sql = """
        SELECT r.name
        FROM sys_users AS u
        JOIN sys_users_roles AS ur ON u.user_id = ur.user_id
        JOIN sys_roles  AS r ON r.role_id = ur.role_id
        WHERE username = %s
    """
    # 查询
    roles = Query(sql, (username,))
    return [r['name'] for r in roles]

if __name__ == "__main__":
    print(SysUsersWithRoles())
    #print(Sentiments())
    #print(SysUser('Administer'))
    #print(SysUserRoles('Administer'))