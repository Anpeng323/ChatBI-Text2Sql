"""应用配置：通过 pydantic-settings 读取环境变量，集中管理 MiniMax、数据库与限流参数。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ===== MiniMax 模型 =====
    minimax_api_key: str = ""
    minimax_model: str = "MiniMax-Text-01"
    minimax_base_url: str = "https://api.minimax.chat/v1"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 2048
    llm_timeout: int = 60
    llm_max_retries: int = 3

    # ===== 数据库连接 =====
    # 本期仅 MySQL；连接层已抽象，后续可扩展其它适配器
    db_url: str = "mysql+pymysql://user:password@127.0.0.1:3306/ubr?charset=utf8mb4"
    db_connect_timeout: int = 10
    db_pool_size: int = 10
    db_max_overflow: int = 20
    # MySQL 查询最大执行时间（毫秒），防止慢查询拖垮数据库
    db_max_execution_time_ms: int = 15000

    # ===== 查询与限流 =====
    max_result_rows: int = 200          # 图表/预览截断行数
    export_max_rows: int = 50000        # 导出全量上限
    retry_on_sql_error: bool = True     # SQL 执行失败自动修正一次
    default_chart_limit: int = 30       # 图表采样行数

    # ===== 服务 =====
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    cors_allow_origins: str = "*"       # 逗号分隔，生产环境请收紧


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
