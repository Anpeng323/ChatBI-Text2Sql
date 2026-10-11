"""数据接入层。"""
from .base import DatabaseAdapter
from .mysql_adapter import MySQLAdapter

__all__ = ["DatabaseAdapter", "MySQLAdapter"]
