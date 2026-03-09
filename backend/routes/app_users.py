from flask import  Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import Query, Delete, Update

users_bp = Blueprint("users", __name__, url_prefix='/users')

# 用户查询
@users_bp.route('/query', methods=['GET'])
@jwt_required()
def query_users():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'admin' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    usernames_str = request.args.get('usernames', '')
    usernames = usernames_str.split() if usernames_str else []
    # 查询
    try:
        users = Query.SysUsersWithRoles(usernames=usernames)
    except Exception as e:
        return jsonify({"message": "查询时发生错误：" + str(e)}), 500
    for u in users:
        u['is_active'] = True if u['is_active'] == 1 else False
    return jsonify({"users": users})

# 删除用户
@users_bp.route('/delete', methods=['POST'])
@jwt_required()
def delete_users():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'admin' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    data = request.json
    user_ids = data.get('user_ids')
    # 删除
    try:
        existing_users = Query.User_Ids(user_ids=user_ids)
        deleted_ids = [u['user_id'] for u in existing_users]
        Delete.SysUsers(user_ids=user_ids)        
    except Exception as e:
        return jsonify({"message": "删除时发生错误：" + str(e)}), 500
    return jsonify({"deleted_ids": deleted_ids})

# 用户批处理（激活 / 冻结 / 重置密码）
@users_bp.route('/batch_update', methods=['POST'])
@jwt_required()
def batch_update_users():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'admin' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    data = request.json
    user_ids = data.get('user_ids')
    action = data.get('action')
    try:
        existing_users = Query.User_Ids(user_ids=user_ids)
        updated_ids = [u['user_id'] for u in existing_users]
        match action:
            case 'activate':
                Update.Update_SysUsersActive(user_ids=user_ids, is_active=True)
            case 'freeze':
                Update.Update_SysUsersActive(user_ids=user_ids, is_active=False)
            case 'reset_password':
                password = data.get('password')
                Update.Update_SysUsersPassword(user_ids=user_ids, password=password)
            case _:
                return jsonify({"message": "未知的处理类型"}), 401
    except Exception as e:
        return jsonify({"message": "处理时发生错误：" + str(e)}), 500
    return jsonify({"updated_ids": updated_ids})

# 用户角色设置
@users_bp.route('/batch_set_role', methods=['POST'])
@jwt_required()
def batch_set_role_users():
    username = get_jwt_identity()
    roles = Query.SysUserRoles(username)
    if not 'admin' in roles:
        return jsonify({"message": "用户没有执行该操作的权限"}), 401
    # 参数处理
    data = request.json
    user_ids = data.get('user_ids')
    role = data.get('role')
    action = data.get('action')
    try:
        match action:
            case 'add':
                Update.Update_SysUsersRole(user_ids=user_ids, role=role, add=True)
            case 'remove':
                Update.Update_SysUsersRole(user_ids=user_ids, role=role, add=False)
            case _:
                return jsonify({"message": "未知的处理类型"}), 401
    except Exception as e:
        return jsonify({"message": "处理时发生错误：" + str(e)}), 500
    # 查询
    try:
        updated_users = Query.SysUsersWithRoles(user_ids=user_ids)
    except Exception as e:
        return jsonify({"message": "查询时发生错误：" + str(e)}), 500
    for u in updated_users:
        u['is_active'] = True if u['is_active'] == 1 else False
    return jsonify({"updated_users": updated_users})

