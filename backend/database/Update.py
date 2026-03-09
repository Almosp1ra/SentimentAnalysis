from database.DbConnection import ConnectDatabase
from tools.SentimentAnalysis import SentimentAnalysisBatch
from tools.PasswordEncrypt import EncryptPassword
from database import Query

# ---------------------------
# 更新执行函数
# ---------------------------
def Execute(sql, params):
    conn = ConnectDatabase()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    conn.commit()
    cursor.close()
    conn.close()
    return

# ---------------------------
# 对外接口
# ---------------------------

# 更新帖子的分析记录
def ReanalyzePosts(post_ids, model):
    # 参数处理
    posts = Query.Post_Contents(post_ids=post_ids)
    contents = [p['content'] for p in posts]
    # 情感分析
    sentiments_batch = SentimentAnalysisBatch(contents, modelList=[model])
    sentiments_new = []
    for i, post in enumerate(posts):
        record = sentiments_batch[i][0]
        record['post_id'] = post['post_id']
        sentiments_new.append(record)
    # 插入新的分析记录 SQL
    if sentiments_new:
        values_list = []
        params = []
        sql = f"""
            INSERT INTO sentiments (post_id, score, type, model, analysis_time)
            VALUES
        """
        for s in sentiments_new:
            values_list.append("(%s,%s,%s,%s,%s)")
            params.extend([s['post_id'], s['score'], s['type'], s['model'], s['analysis_time']])
        sql += ", ".join(values_list)
        sql += f""" 
            ON DUPLICATE KEY UPDATE
            score = VALUES(score),
            type = VALUES(type),
            model = VALUES(model),
            analysis_time = VALUES(analysis_time)
        """
        Execute(sql, tuple(params))
    return True

# 激活或冻结用户
def Update_SysUsersActive(user_ids, is_active=True):
    # 构造 sql
    params = []
    sql = f"""
        UPDATE sys_users
        SET is_active = {1 if is_active else 0}
        WHERE user_id IN ({",".join(["%s"] * len(user_ids))})
    """
    params.extend(user_ids)
    Execute(sql, tuple(params))
    return True

# 重置用户密码
def Update_SysUsersPassword(user_ids, password):
    password_hash = EncryptPassword(password=password)
    # 构造 sql
    params = []
    sql = f"""
        UPDATE sys_users
        SET password_hash = '{password_hash}'
        WHERE user_id IN ({",".join(["%s"] * len(user_ids))})
    """
    params.extend(user_ids)
    Execute(sql, tuple(params))
    return True

# 更新多个用户的角色
def Update_SysUsersRole(user_ids, role, add=True):
    # 查询角色的 id
    roles = Query.SysRoles()
    roleIdDict = { r['name']: r['role_id'] for r in roles }
    role_id = roleIdDict[role]
    # 构造参数表
    if add:
        values_list = []
        params = []
        for user_id in user_ids:
            values_list.append("(%s, %s)")
            params.extend([user_id, role_id])
        if not values_list:
            return
        sql = f"""
            INSERT IGNORE INTO sys_users_roles (user_id, role_id)
            VALUES {", ".join(values_list)}
        """
    else:
        params = []
        params.extend(user_ids)
        params.append(role_id)
        sql = f"""
            DELETE FROM sys_users_roles
            WHERE user_id IN ({",".join(["%s"] * len(user_ids))}) AND role_id = %s
        """
    Execute(sql, tuple(params))
    return True

if __name__ == "__main__":
    Update_SysUsersRole([1], 'analyst')