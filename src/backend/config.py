from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):
    model_config_dict = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    db_user: str
    db_pass: str
    db_host: str
    db_port: int
    db_name: str
