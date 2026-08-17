from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    events_path: Path = Path("data/events.csv")
    products_path: Path = Path("data/products.csv")
    model_path: Path = Path("model/model.pkl")
    top_n_recommendations: int = 10
    cold_start_window_days: int = 30
    log_level: str = "INFO"


config = Config()
