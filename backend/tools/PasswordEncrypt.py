import bcrypt

"""
用户密码加密与校验
"""

# 密码加密程序
def EncryptPassword(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

# 密码检查
def CheckPassword(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

if __name__ == "__main__":
    password = "admin123"  # 管理员初始密码
    print(EncryptPassword(password))