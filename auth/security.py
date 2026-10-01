from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

SECRET_KEY = "iboughtabike"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str,hashed_password: str) -> bool:
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if not username:
            return None

        return username

    except JWTError:
        return None