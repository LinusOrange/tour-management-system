import os
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

# 核心修改：从环境变量中安全读取密钥
# 变量名必须与 .env 中的 APP_SECRET_KEY 保持一致
SECRET_KEY = os.getenv("APP_SECRET_KEY")
ALGORITHM = "HS256"

# 安全性熔断：如果环境变量未配置，则拒绝启动，防止系统运行在不安全状态
if not SECRET_KEY:
    raise ValueError("Critical Error: APP_SECRET_KEY is not set in environment variables.")

# 配置加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    """
    对密码进行哈希处理
    只要 bcrypt 版本固定为 3.2.0，即可兼容 72 字节以上的长密码
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """校验明文密码与哈希值"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    """生成 JWT Token"""
    to_encode = data.copy()
    # 令牌有效期建议设置为 24 小时，满足全天研学工作的连续性
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)