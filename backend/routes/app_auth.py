from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

from database import Query, Update
from database.Insert import Insert_SysUser
from tools.PasswordEncrypt import CheckPassword

auth_bp = Blueprint("auth", __name__, url_prefix='/auth')

# 登录
@auth_bp.route('/login', methods=['POST'])
def auth_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    try:
        user = Query.SysUser(username)
        if not user or not CheckPassword(password, user['password_hash']):
            return jsonify({"message": "用户名或密码错误"}), 401
        if user['is_active'] != 1:
            return jsonify({"message": "该用户已被冻结，请联系管理员重新激活"}), 401
    except Exception as e:
        return jsonify({"message": "登录发生错误：" + str(e)}), 500
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    return jsonify({"access_token": access_token, "refresh_token": refresh_token, "username": user['username']})

# 注册
@auth_bp.route('/register', methods=['POST'])
def auth_register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    try:
        user = Query.SysUser(username)
        if user:
            return jsonify({"message": "该用户名已被注册"}), 401
        Insert_SysUser(username=username, password=password, roles=['ingest'])
    except Exception as e:
        return jsonify({"message": "注册时发生错误：" + str(e)}), 500
    return jsonify({})

# 刷新 Access Token
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def auth_refresh():
    username = get_jwt_identity()
    new_access_token = create_access_token(identity=username)
    return jsonify({"access_token": new_access_token})

# 获取用户信息
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def auth_me():
    username = get_jwt_identity()
    try:
        user = Query.SysUser(username)
        if not user:
            return jsonify({"message": "用户不存在"}), 404
        roles = Query.SysUserRoles(username)
    except Exception as e:
        return jsonify({"message": "验证时发生错误：" + str(e)}), 500
    return jsonify({
        "username": username,
        "roles": roles
    })

# 修改密码
@auth_bp.route('/modify_password', methods=['POST'])
@jwt_required()
def auth_modify_password():
    username = get_jwt_identity()
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    try:
        user = Query.SysUser(username)
        if not user:
            return jsonify({"message": "未查找到用户，请联系管理员修复该错误"}), 500
        if not CheckPassword(old_password, user['password_hash']):
            return jsonify({"message": "密码错误"}), 401
    except Exception as e:
        return jsonify({"message": "密码校验时发生错误：" + str(e)}), 500
    try:
        Update.Update_SysUsersPassword([user['user_id']], new_password)
    except Exception as e:
        return jsonify({"message": "修改密码时发生错误：" + str(e)}), 500
    return jsonify({})