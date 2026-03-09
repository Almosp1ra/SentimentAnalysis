from database.DbConnection import ConnectDatabase

# ---------------------------
# 删除执行函数
# ---------------------------
def Execute(sql, params):
    conn = ConnectDatabase()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    conn.commit()
    cursor.close()
    conn.close()
    return True

# ---------------------------
# 对外接口
# ---------------------------

# 删帖子
def Posts(post_ids):
    # where 语句生成
    where_clauses = []
    params = []
    # post id
    if post_ids:
        where_clauses.append(f"post_id IN ({",".join(["%s"] * len(post_ids))})")
        params.extend(post_ids)
    # 拼接 SQL
    sql = f"""
        DELETE FROM posts
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
    """
    # 删除
    return Execute(sql, tuple(params))

# 删情感分析结果
def Sentiments(post_ids, models):
    # where 语句生成
    where_clauses = []
    params = []
    # post id
    if post_ids:
        where_clauses.append(f"post_id IN ({",".join(["%s"] * len(post_ids))})")
        params.extend(post_ids)
    # 情感分析模型
    if models:
        where_clauses.append(f"model IN ({",".join(["%s"] * len(models))})")
        params.extend(models)
    # 拼接 SQL
    sql = f"""
        DELETE FROM sentiments
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
    """
    # 删除
    return Execute(sql, tuple(params))

# 删用户
def SysUsers(user_ids):
    # where 语句生成
    where_clauses = []
    params = []
    # user_ids
    if user_ids:
        where_clauses.append(f"user_id IN ({",".join(["%s"] * len(user_ids))})")
        params.extend(user_ids)
    # 拼接 SQL
    sql = f"""
        DELETE FROM sys_users
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
    """
    # 删除
    return Execute(sql, tuple(params))

# 删用户的所有角色
def SysUsersRoles(user_ids):
    # where 语句生成
    where_clauses = []
    params = []
    # user_ids
    if user_ids:
        where_clauses.append(f"user_id IN ({",".join(["%s"] * len(user_ids))})")
        params.extend(user_ids)
    # 拼接 SQL
    sql = f"""
        DELETE FROM sys_users_roles
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
    """
    # 删除
    return Execute(sql, tuple(params))

if __name__ == "__main__":
    Posts(post_ids=[1])