# 使用Debian的Python镜像
FROM python:3-slim

# 设置作者或维护者信息（可选）
LABEL maintainer="your_email@example.com"

# 设置环境变量来禁止Python写入pyc文件和缓冲stdout和stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 使用apt安装必要的依赖，然后清理缓存以减小镜像大小
RUN apt-get update \
    && apt-get install -y --no-install-recommends git libxslt-dev libffi-dev libssl-dev make cmake \
    && echo "Asia/Shanghai" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata

# 设置工作目录
WORKDIR /app

# 克隆项目仓库
RUN git clone https://github.com/olixu/stocktrend.git .

# 复制整个项目到工作目录
COPY . /app

# 安装Python依赖
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 清理不再需要的包和缓存
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 暴露端口（假设你的应用使用的是8080端口）
EXPOSE 8080

# 设置运行时的默认命令
CMD ["python", "main.py"]
