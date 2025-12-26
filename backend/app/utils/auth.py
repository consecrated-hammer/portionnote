from passlib.context import CryptContext

PasswordContext = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def HashPassword(Password: str) -> str:
    return PasswordContext.hash(Password)


def VerifyPassword(Password: str, PasswordHash: str) -> bool:
    return PasswordContext.verify(Password, PasswordHash)
