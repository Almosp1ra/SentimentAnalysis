from database.DbConnection import ConnectDatabase
from tools.PasswordEncrypt import EncryptPassword
from database import Query
import hashlib

# ---------------------------
# 数据处理
# ---------------------------

# 计算 content_hash
def calc_md5(s):
    if s is None:
        s = ''
    if isinstance(s, str):
        b = s.encode('utf-8')
    else:
        b = str(s).encode('utf-8')
    return hashlib.md5(b).hexdigest()

# chunk
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

# 批量查询已有 users，构造字典映射
def Users_Map(cursor, user_keys, batch_chunk):
    users_map = {}  # (username,platform) -> user_id
    user_key_list = list(user_keys)
    if user_key_list:
        for chunk in chunks(user_key_list, batch_chunk):
            sql = f"SELECT username, platform, user_id FROM users WHERE (username, platform) IN ({",".join(["(%s,%s)"] * len(chunk))})"
            params = []
            for k in chunk:
                params.extend(k)
            cursor.execute(sql, params)
            for r in cursor.fetchall():
                users_map[(r['username'], r['platform'])] = r['user_id']
    return users_map

# 批量查询已有 topics，构造字典映射
def Topics_Map(cursor, topics_set, batch_chunk):
    topics_map = {} # topic -> topic_id
    topics_list = list(topics_set)
    if topics_list:
        for chunk in chunks(topics_list, batch_chunk):
            sql = f"SELECT topic, topic_id FROM topics WHERE topic IN ({",".join(["%s"] * len(chunk))})"
            cursor.execute(sql, list(chunk))
            for r in cursor.fetchall():
                topics_map[r['topic']] = r['topic_id']
    return topics_map

# 批量查询已有 keywords，构造字典映射
def Keywords_Map(cursor, keywords_set, batch_chunk):
    keywords_map = {} # keywords -> keywords_map
    keywords_list = list(keywords_set)
    if keywords_list:
        for chunk in chunks(keywords_list, batch_chunk):
            sql = f"SELECT keyword, keyword_id FROM keywords WHERE keyword IN ({",".join(["%s"] * len(chunk))})"
            cursor.execute(sql, list(chunk))
            for r in cursor.fetchall():
                keywords_map[r['keyword']] = r['keyword_id']
    return keywords_map

# 批量查询已有 posts，构造字典映射
def Posts_Map(cursor, post_keys, users_map, batch_chunk):
    posts_map = {}  # (username,platform,content_hash,create_time) -> post_id
    post_query_tuples = []
    for (username, platform, ch, ctime, rec) in post_keys:
        uid = users_map.get((username, platform))
        if uid:
            post_query_tuples.append((uid, ch, ctime))
    if post_query_tuples:
        for chunk in chunks(post_query_tuples, batch_chunk):
            sql = f"""
                SELECT p.post_id, p.user_id, p.content_hash, p.create_time, u.username, u.platform
                FROM posts p
                JOIN users u ON p.user_id = u.user_id
                WHERE (p.user_id, p.content_hash, p.create_time) IN ({",".join(["(%s,%s,%s)"] * len(chunk))})
            """
            params = []
            for tup in chunk:
                params.extend(tup)
            cursor.execute(sql, params)
            for r in cursor.fetchall():
                key = (r['username'], r['platform'], r['content_hash'], r['create_time'])
                posts_map[key] = r['post_id']
    return posts_map

# ---------------------------
# 插入 user、post、sentiment
# ---------------------------

def Insert_User(cursor, user_data):
    cursor.execute("""
        INSERT IGNORE INTO users (username, platform, gender, birthday)
        VALUES (%s, %s, %s, %s)
    """, (
        user_data.get('username'),
        user_data.get('platform'),
        user_data.get('gender'),
        user_data.get('birthday')
    ))
    user_id = cursor.lastrowid
    if not user_id:
        cursor.execute("SELECT user_id FROM users WHERE username=%s AND platform=%s", (user_data.get('username'), user_data.get('platform')))
        row = cursor.fetchone()
        if row:
            user_id = row['user_id']
    return user_id

def Insert_Post(cursor, post_data, user_id):
    cursor.execute("""
        INSERT IGNORE INTO posts (user_id, content, location, create_time, content_hash)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        user_id,
        post_data.get('content'),
        post_data.get('location'),
        post_data.get('create_time'),
        post_data.get('content_hash')
    ))
    post_id = cursor.lastrowid
    if not post_id:
        cursor.execute("SELECT post_id FROM posts WHERE user_id=%s AND content_hash=%s AND create_time=%s", (user_id, post_data.get('content_hash'), post_data.get('create_time')))
        row = cursor.fetchone()
        if row:
            post_id = row['post_id']
    return post_id

def Insert_Sentiment(cursor, sentiment_data, post_id):
    cursor.execute("""
        INSERT IGNORE INTO sentiments (post_id, score, type, model, analysis_time)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        post_id,
        sentiment_data.get('score'),
        sentiment_data.get('type'),
        sentiment_data.get('model'),
        sentiment_data.get('analysis_time')
    ))

# ---------------------------
# Insert_Data、批量加速
# ---------------------------
def Insert_Data(standardRecords, batch_chunk=800):
    if not standardRecords:
        return
    conn = ConnectDatabase()
    cursor = conn.cursor(dictionary=True)
    try:
        # 关闭自动提交以包裹在单个事务中，减少磁盘 flush 次数
        conn.autocommit = False
        # 收集 users、posts、topics、keywords 的唯一 keys
        user_keys = set()
        topics_set = set()
        keywords_set = set()
        post_keys = []
        for rec in standardRecords:
            username = rec.get('username')
            platform = rec.get('platform')
            user_keys.add((username, platform))
            for t in (rec.get('topics') or []):
                topics_set.add(t)
            for kw in (rec.get('keywords') or []):
                keywords_set.add(kw)
            # 计算 content_hash
            ch = calc_md5(rec.get('content'))
            rec['content_hash'] = ch
            post_keys.append((username, platform, ch, rec.get('create_time'), rec))
        # 构造已有 users、topics、keywords、posts 的字典映射
        users_map = Users_Map(cursor, user_keys, batch_chunk)  # (username,platform) -> user_id
        topics_map = Topics_Map(cursor, topics_set, batch_chunk) # topic -> topic_id
        keywords_map = Keywords_Map(cursor, keywords_set, batch_chunk) # keywords -> keywords_map
        posts_map = Posts_Map(cursor, post_keys, users_map, batch_chunk)  # (username,platform,content_hash,create_time) -> post_id
        # 去重、插入
        for rec in standardRecords:
            ukey = (rec.get('username'), rec.get('platform'))
            ch = rec.get('content_hash')
            pkey = (rec.get('username'), rec.get('platform'), ch, rec.get('create_time'))
            if pkey in posts_map:   # post 已存在，跳过
                continue
            # 插入 user
            user_id = users_map.get(ukey)
            if user_id is None:
                user_id = Insert_User(cursor, {
                    'username': rec.get('username'),
                    'platform': rec.get('platform'),
                    'gender': rec.get('gender'),
                    'birthday': rec.get('birthday')
                })
                users_map[ukey] = user_id
            # 插入 post (with content_hash)
            post_id = Insert_Post(cursor, rec, user_id)
            posts_map[pkey] = post_id
            # 插入 topics
            for t in (rec.get('topics') or []):
                tid = topics_map.get(t)
                if tid is None:
                    cursor.execute("INSERT IGNORE INTO topics (topic, description) VALUES (%s, %s)", (t, None))
                    tid = cursor.lastrowid
                    topics_map[t] = tid
                if tid:
                    cursor.execute("INSERT IGNORE INTO posts_topics (post_id, topic_id) VALUES (%s, %s)", (post_id, tid))
            # 插入 keywords
            for kw in (rec.get('keywords') or []):
                kid = keywords_map.get(kw)
                if kid is None:
                    cursor.execute("INSERT IGNORE INTO keywords (keyword) VALUES (%s)", (kw,))
                    kid = cursor.lastrowid
                    keywords_map[kw] = kid
                if kid:
                    cursor.execute("INSERT IGNORE INTO posts_keywords (post_id, keyword_id) VALUES (%s, %s)", (post_id, kid))
            # 插入 sentiments
            for s in (rec.get('sentiments') or []):
                Insert_Sentiment(cursor, s, post_id)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# 插入系统用户，可选择顺带插入角色
def Insert_SysUser(username, password, roles=None):
    conn = ConnectDatabase()
    cursor = conn.cursor(dictionary=True)    
    try:
        # 插入用户
        cursor.execute("""
            INSERT INTO sys_users (username, password_hash)
            VALUES (%s, %s)
        """, (username, EncryptPassword(password)))
        user_id = cursor.lastrowid
        # 插入角色
        if roles:
            values_list = []
            params = []
            roleIdDict = { r['name']: r['role_id'] for r in Query.SysRoles() }
            for r in roles or []:
                rid = roleIdDict[r]
                values_list.append("(%s, %s)")
                params.extend([user_id, rid])
            if not values_list:
                return
            sql = f"""
                INSERT IGNORE INTO sys_users_roles (user_id, role_id)
                VALUES {", ".join(values_list)}
            """
            cursor.execute(sql, tuple(params))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    0