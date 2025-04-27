# GCPにFastAPIアプリをデプロイするためのDockerfile

# ベースイメージを指定（軽量なPython 3.9の公式イメージ）
FROM python:3.9-slim

# 作業ディレクトリを作成（コンテナ内で作業するディレクトリ）
WORKDIR /app

# 必要なパッケージをインストール
RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションに必要なフォルダをコンテナにコピー
COPY . .

# ポートを公開
EXPOSE 8080

# docker run時に実行するコマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]