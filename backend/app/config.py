from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    amap_api_key: str = ""
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    llm_fast_model: str = ""  # 规划用快速模型，为空则复用 llm_model
    host: str = "0.0.0.0"
    port: int = 8000

    # Memory / Checkpointer
    memory_type: str = "sqlite"  # sqlite | postgres
    memory_db_path: str = "travel_plans.db"  # sqlite 文件路径

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
