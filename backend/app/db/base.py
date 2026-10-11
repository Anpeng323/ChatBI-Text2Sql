"""数据库连接抽象基类。

通用 ChatBI 平台的数据接入点：本期仅实现 MySQLAdapter，
但所有编排逻辑只依赖 DatabaseAdapter 接口，今后新增
PostgreSQL / SQLite / CSV 适配器无需改动上层代码。
"""
from abc import ABC, abstractmethod

import pandas as pd


class DatabaseAdapter(ABC):
    """数据源统一接口。"""

    @abstractmethod
    def execute_query(self, sql: str) -> pd.DataFrame:
        """执行已校验的只读 SQL，返回结果 DataFrame。"""
        raise NotImplementedError

    @abstractmethod
    def probe_schema(self) -> dict:
        """探测并返回 schema 描述（表/字段/类型/注释），供提示词注入。"""
        raise NotImplementedError

    def health_check(self) -> bool:
        """连通性检查，默认 ping。"""
        try:
            self.execute_query("SELECT 1")
            return True
        except Exception:
            return False
