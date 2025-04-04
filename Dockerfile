# 使用官方Python基础镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 复制当前目录的内容到工作目录
COPY . /app

# 直接安装所需的Python包
RUN pip install --no-cache-dir Flask Flask-Limiter requests

# 暴露端口
EXPOSE 3000

# 设置环境变量（可选，实际运行时可以通过 `-e` 指定）
# ENV SECRET=my_secret_key

# 启动应用
CMD ["python", "app.py"]