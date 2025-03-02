FROM python:3.13-slim

WORKDIR /scripts

# タイムゾーンを日本時間(JST)に設定
ENV TZ=Asia/Tokyo


# 基本パッケージと PostgreSQL 16 のリポジトリを追加
RUN apt-get update && apt-get install -y curl gnupg lsb-release software-properties-common tzdata && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# PGroonga のリポジトリを追加 (Debian 用)
RUN curl -fsSL https://packages.groonga.org/debian/groonga-apt-source-latest-$(lsb_release -cs).deb -o groonga-apt-source.deb && \
    apt-get update && apt-get install -y ./groonga-apt-source.deb && \
    rm groonga-apt-source.deb && \
    apt-get update

# Arrow のリポジトリを追加
RUN apt-get update && apt-get install -y ca-certificates lsb-release wget && \
    wget https://apache.jfrog.io/artifactory/arrow/$(lsb_release --id --short | tr 'A-Z' 'a-z')/apache-arrow-apt-source-latest-$(lsb_release --codename --short).deb && \
    apt-get update && apt-get install -y ./apache-arrow-apt-source-latest-$(lsb_release --codename --short).deb && \
    rm -f apache-arrow-apt-source.deb && \
    apt-get update

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    postgresql-16 \
    postgresql-client-16 \
    postgresql-16-repack \
    redis-tools \
    curl \
    python3-arrow \
    && rm -rf /var/lib/apt/lists/*

# Minio Client (mc) のインストール
RUN curl -O https://dl.min.io/client/mc/release/linux-amd64/mc && \
    chmod +x mc && \
    mv mc /usr/local/bin/

RUN pip install --upgrade pip && \
    pip install python-dotenv schedule requests psutil

# バックアップディレクトリを作成
RUN mkdir -p /backup/pg_dump/manual/ && \
    chmod -R 777 /backup

CMD ["python", "main.py"]
