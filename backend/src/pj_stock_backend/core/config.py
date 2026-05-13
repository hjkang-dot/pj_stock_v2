from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PJ Stock Backend"
    environment: str = "local"
    database_url: str = "sqlite:///../data/app.db"
    dart_api_key: str = ""
    krx_api_key: str = ""


    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
