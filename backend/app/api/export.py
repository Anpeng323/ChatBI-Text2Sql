"""导出接口：导出查询结果为 CSV（图表 PNG 由前端 ECharts getDataURL 完成）。"""
from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..core.config import settings
from ..db.mysql_adapter import MySQLAdapter

router = APIRouter(prefix="/api", tags=["export"])

_adapter = MySQLAdapter()


@router.get("/export/csv")
async def export_csv(sql: str, filename: str = "chatbi_export") -> StreamingResponse:
    """按 SQL 导出 CSV（上限 export_max_rows 行）。"""
    try:
        df = _adapter.execute_query(sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"查询失败：{e}")
    if len(df) > settings.export_max_rows:
        df = df.head(settings.export_max_rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    buf.seek(0)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}.csv"'
    }
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers=headers)
