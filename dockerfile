# 使用與你專案相同的 Python 版本
FROM python:3.11-slim

# 從官方的 uv image 中把 uv 複製過來使用
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 複製 uv 的專案設定檔
COPY pyproject.toml uv.lock ./

# 使用 uv 進行同步安裝（速度比 pip 快非常多，且不需要 requirements.txt）
RUN uv sync --frozen --no-cache

# 複製其他原始碼
COPY . .

EXPOSE 5000

# 透過 uv 的環境來執行 Flask
CMD ["uv", "run", "python", "app.py"]