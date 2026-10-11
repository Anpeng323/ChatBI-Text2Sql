"""MySQL 适配器：复用连接池执行只读查询，并探测 information_schema。"""
from __future__ import annotations

from sqlalchemy import create_engine, text

import pandas as pd

from ..core.config import settings
from ..core.security import validate_sql
from .base import DatabaseAdapter


class MySQLAdapter(DatabaseAdapter):
    def __init__(self) -> None:
        self._engine = create_engine(
            settings.db_url,
            connect_args={"connect_timeout": settings.db_connect_timeout},
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
        )

    def execute_query(self, sql: str) -> pd.DataFrame:
        safe_sql = validate_sql(sql, max_limit=settings.max_result_rows)
        # 兜底超时（MySQL 语法），其它方言适配器自行实现
        wrapped = text(
            f"SELECT /*+ MAX_EXECUTION_TIME({settings.db_max_execution_time_ms}) */ "
            f"* FROM ({safe_sql.rstrip(';')}) AS _subq"
            if safe_sql.lower().startswith("select")
            else safe_sql
        )
        return pd.read_sql(wrapped, self._engine)

    def probe_schema(self) -> dict:
        """读取当前库的表与字段，生成结构描述。

        返回结构：
        {
          "dialect": "mysql",
          "tables": [
            {"name": "...", "comment": "...", "columns": [
              {"name": "...", "type": "...", "comment": "..."}
            ]}
          ]
        }
        """
        tables_sql = text(
            "SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' "
            "ORDER BY TABLE_NAME"
        )
        cols_sql = text(
            "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT "
            "FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME, ORDINAL_POSITION"
        )
        with self._engine.connect() as conn:
            tables = conn.execute(tables_sql).mappings().all()
            columns = conn.execute(cols_sql).mappings().all()

        by_table: dict[str, list[dict]] = {}
        for c in columns:
            by_table.setdefault(c["TABLE_NAME"], []).append(
                {
                    "name": c["COLUMN_NAME"],
                    "type": c["COLUMN_TYPE"],
                    "comment": c["COLUMN_COMMENT"] or "",
                }
            )

        table_list = []
        for t in tables:
            name = t["TABLE_NAME"]
            table_list.append(
                {
                    "name": name,
                    "comment": t["TABLE_COMMENT"] or "",
                    "columns": by_table.get(name, []),
                }
            )
        return {"dialect": "mysql", "tables": table_list}
