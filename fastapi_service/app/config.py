from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    JWT_SIGNING_KEY: str = "dev-insecure-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    DATABASE_URL: str = "mysql+pymysql://root:@127.0.0.1:3306/ccps"
    PAYMENT_SUCCESS_RATE: float = 0.8
    MAX_PAYMENT_AMOUNT: float = 100000
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"


settings = Settings()
