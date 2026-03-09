from flask import Flask, jsonify, render_template
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# 导入蓝图对象
from routes.app_visual import visual_bp
from routes.app_auth import auth_bp
from routes.app_posts import posts_bp
from routes.app_users import users_bp

# 初始化
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.config['JWT_SECRET_KEY'] = 'Yggdrasil'
jwt = JWTManager(app)
CORS(app)

# token 错误处理回调
# 1) 未提供 token（Missing Authorization Header）
@jwt.unauthorized_loader
def custom_unauthorized_callback(reason):
    return jsonify({"message": "缺少授权头，登录以获取 token", "error": reason}), 401

# 2) token 无效（签名错误 / 格式错 / tampered）
@jwt.invalid_token_loader
def custom_invalid_token_callback(reason):
    return jsonify({"message": "无效的 token", "error": reason}), 422

# 3) token 过期（expired）
@jwt.expired_token_loader
def custom_expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"message": "token 已过期，请重新登录"}), 401

# 注册蓝图
app.register_blueprint(visual_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(users_bp)

"""
@app.route("/")
def index():
    return render_template("index.html")
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)