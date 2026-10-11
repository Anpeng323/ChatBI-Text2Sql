# ---- 阶段 1：构建前端 ----
FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- 阶段 2：后端运行镜像 ----
FROM python:3.11-slim AS backend
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 系统依赖（pymysql 纯 Python，无需编译；保留 build 基础以防个别包）
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
# 把构建好的前端产物放入 backend/frontend/dist，由 main.py 直接托管
COPY --from=frontend /frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
