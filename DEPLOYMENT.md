# NewPro 项目部署指南

## 📋 目录
1. [项目架构](#项目架构)
2. [后端部署](#后端部署)
3. [前端部署](#前端部署)
4. [生产环境配置](#生产环境配置)
5. [Docker部署(推荐)](#docker部署)
6. [传统部署方式](#传统部署方式)
7. [监控与维护](#监控与维护)

---

## 🏗️ 项目架构

```
newpro/
├── backend/          # FastAPI 后端服务
│   ├── app/         # 应用代码
│   ├── alembic/     # 数据库迁移
│   ├── storage/     # 文件存储
│   └── requirements.txt
├── frontend/        # Vue.js 前端
│   ├── src/        # 源代码
│   └── dist/       # 构建后的静态文件
├── docker-compose.yml
└── nginx.conf
```

**服务端口:**
- 后端API: 8000 (内部) → 8008 (外部)
- 前端: 5173 (开发) → 80/443 (生产)
- 数据库: 5432 (内部)

---

## 🔧 后端部署

### 方式1: Docker部署 (推荐)

#### 1.1 准备Docker镜像

后端已配置好Dockerfile,使用以下命令构建:

```bash
cd newpro
docker-compose build backend
```

#### 1.2 配置环境变量

编辑 `backend/.env`:

```env
# 数据库配置 (生产环境请使用强密码)
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_password@db:5432/starpy

# 应用配置
SECRET_KEY=your_production_secret_key_min_32_chars
DEBUG=False
ENVIRONMENT=production

# CORS配置 (替换为你的前端域名)
ALLOWED_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# API配置 (替换为你的后端域名)
API_URL=https://api.yourdomain.com

# 文件上传配置
UPLOAD_DIR=./storage
MAX_UPLOAD_SIZE=5242880

# 数据库连接池配置
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

#### 1.3 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

#### 1.4 运行数据库迁移

```bash
docker-compose exec backend alembic upgrade head
```

#### 1.5 验证部署

```bash
# 测试健康检查
curl http://localhost:8008/health

# 访问API文档
curl http://localhost:8008/docs
```

---

### 方式2: 传统部署

#### 2.1 安装Python环境

```bash
# 安装Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# 创建虚拟环境
cd newpro/backend
python3.11 -m venv venv
source venv/bin/activate
```

#### 2.2 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.3 配置环境变量

创建 `backend/.env` 文件 (同Docker方式)

#### 2.4 运行数据库迁移

```bash
alembic upgrade head
```

#### 2.5 使用Gunicorn运行

```bash
# 安装Gunicorn
pip install gunicorn uvicorn[standard]

# 运行服务 (4个worker进程)
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info
```

#### 2.6 配置Systemd服务

创建 `/etc/systemd/system/newpro-backend.service`:

```ini
[Unit]
Description=NewPro FastAPI Backend
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/newpro/backend
Environment="PATH=/opt/newpro/backend/venv/bin"
ExecStart=/opt/newpro/backend/venv/bin/gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /opt/newpro/backend/logs/access.log \
  --error-logfile /opt/newpro/backend/logs/error.log
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable newpro-backend
sudo systemctl start newpro-backend
sudo systemctl status newpro-backend
```

---

## 🎨 前端部署

### 3.1 构建生产版本

```bash
cd newpro/frontend

# 安装依赖 (如果还没安装)
npm install

# 构建生产版本
npm run build
```

这会在 `frontend/dist/` 目录生成优化后的静态文件。

### 3.2 配置API地址

编辑 `frontend/src/api/index.ts`,确保API地址指向生产环境:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.yourdomain.com';
```

或者在构建前设置环境变量:

```bash
# 创建 .env.production 文件
echo "VITE_API_URL=https://api.yourdomain.com" > .env.production

# 构建
npm run build
```

### 3.3 部署方式选择

#### 方式A: Nginx静态托管 (推荐)

**配置Nginx:**

创建 `/etc/nginx/sites-available/newpro`:

```nginx
# 前端服务器
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # SSL配置 (推荐使用Let's Encrypt)
    # listen 443 ssl http2;
    # ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    root /opt/newpro/frontend/dist;
    index index.html;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript;

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Vue Router History模式支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理 (如果需要)
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API服务器 (如果独立域名)
server {
    listen 80;
    server_name api.yourdomain.com;

    # SSL配置
    # listen 443 ssl http2;
    # ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS处理已在FastAPI中配置
        # 如需额外配置可在此添加
    }

    # 文件上传大小限制
    client_max_body_size 10M;
}
```

**启用配置:**

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/newpro /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载Nginx
sudo systemctl reload nginx
```

#### 方式B: Docker Nginx容器

已在 `docker-compose.yml` 中配置,直接使用:

```bash
docker-compose up -d nginx
```

#### 方式C: CDN部署 (性能最优)

**适用于静态资源CDN服务:**

1. **阿里云OSS + CDN:**
```bash
# 安装ossutil
wget http://gosspublic.alicdn.com/ossutil/1.7.14/ossutil64
chmod 755 ossutil64

# 配置
./ossutil64 config

# 上传dist目录
./ossutil64 cp -r frontend/dist/ oss://your-bucket/
```

2. **腾讯云COS + CDN:**
```bash
# 安装COSCMD
pip install coscmd

# 配置
coscmd config -a <SecretId> -s <SecretKey> -b <BucketName> -r <Region>

# 上传
coscmd upload -r frontend/dist/ /
```

3. **Vercel (免费):**
```bash
# 安装Vercel CLI
npm install -g vercel

# 部署
cd frontend
vercel --prod
```

4. **Netlify (免费):**
```bash
# 安装Netlify CLI
npm install -g netlify-cli

# 部署
cd frontend
netlify deploy --prod --dir=dist
```

---

## 🔒 生产环境配置

### 4.1 安全检查清单

**后端安全:**
- [ ] 更改 `SECRET_KEY` 为强随机字符串 (至少32字符)
- [ ] 设置 `DEBUG=False`
- [ ] 配置正确的 `ALLOWED_ORIGINS` (限制CORS)
- [ ] 使用强数据库密码
- [ ] 配置HTTPS (SSL证书)
- [ ] 限制文件上传大小和类型
- [ ] 启用请求速率限制
- [ ] 配置日志记录
- [ ] 定期备份数据库

**前端安全:**
- [ ] 移除console.log和调试代码
- [ ] 启用HTTPS
- [ ] 配置CSP (Content Security Policy)
- [ ] 压缩和混淆代码
- [ ] 配置适当的缓存策略

### 4.2 性能优化

**后端优化:**

```python
# backend/app/core/config.py

# 数据库连接池
DB_POOL_SIZE = 20  # 根据服务器资源调整
DB_MAX_OVERFLOW = 40

# Gunicorn worker数量
# workers = (2 * CPU核心数) + 1
# 例如: 4核CPU → 9个workers
```

**前端优化:**

```javascript
// frontend/vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router'],
          'ui-vendor': ['element-plus']
        }
      }
    },
    chunkSizeWarningLimit: 600
  }
})
```

### 4.3 SSL证书配置 (Let's Encrypt)

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# 自动续期
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## 📊 监控与维护

### 5.1 日志管理

**后端日志:**

```bash
# 查看实时日志
docker-compose logs -f backend

# 或使用journalctl (systemd)
sudo journalctl -u newpro-backend -f

# 日志轮转配置 /etc/logrotate.d/newpro
/opt/newpro/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload newpro-backend
    endscript
}
```

### 5.2 数据库备份

```bash
# 创建备份脚本 /opt/scripts/backup-newpro-db.sh
#!/bin/bash
BACKUP_DIR="/opt/backups/newpro"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Docker方式
docker-compose exec -T db pg_dump -U postgres starpy | gzip > $BACKUP_DIR/starpy_$DATE.sql.gz

# 传统方式
# pg_dump -U postgres starpy | gzip > $BACKUP_DIR/starpy_$DATE.sql.gz

# 保留最近30天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# 添加到crontab
# 0 2 * * * /opt/scripts/backup-newpro-db.sh
```

### 5.3 健康检查

```bash
# 创建监控脚本 /opt/scripts/health-check.sh
#!/bin/bash
API_URL="https://api.yourdomain.com"

# 检查API健康状态
if curl -f -s "$API_URL/health" > /dev/null; then
    echo "✓ API服务正常"
else
    echo "✗ API服务异常"
    # 发送告警 (邮件/短信/企业微信等)
    # systemctl restart newpro-backend
fi

# 检查数据库连接
if docker-compose exec -T db pg_isready -U postgres > /dev/null; then
    echo "✓ 数据库正常"
else
    echo "✗ 数据库异常"
fi

# 添加到crontab
# */5 * * * * /opt/scripts/health-check.sh
```

### 5.4 性能监控

**推荐工具:**
- **APM:** Sentry (错误追踪), New Relic, DataDog
- **日志:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **指标:** Prometheus + Grafana
- **数据库:** pgAdmin, pg_stat_statements

---

## 🚀 快速部署命令

### Docker一键部署 (推荐)

```bash
# 1. 克隆项目
git clone <repository-url> /opt/newpro
cd /opt/newpro/newpro

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 配置生产环境参数

# 3. 构建前端
cd frontend
npm install
npm run build
cd ..

# 4. 启动所有服务
docker-compose up -d

# 5. 运行数据库迁移
docker-compose exec backend alembic upgrade head

# 6. 验证部署
curl http://localhost:8008/health
curl http://localhost:8008/docs
```

### 传统部署命令

```bash
# 1. 后端部署
cd /opt/newpro/newpro/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# 2. 启动后端 (使用systemd或screen)
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --daemon

# 3. 前端构建
cd ../frontend
npm install
npm run build

# 4. 配置Nginx
sudo cp /path/to/nginx.conf /etc/nginx/sites-available/newpro
sudo ln -s /etc/nginx/sites-available/newpro /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 📝 常见问题

### Q1: 如何更新代码?

```bash
# Docker方式
git pull
docker-compose build
docker-compose up -d
docker-compose exec backend alembic upgrade head

# 传统方式
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart newpro-backend
```

### Q2: 如何回滚数据库?

```bash
# 查看迁移历史
docker-compose exec backend alembic history

# 回滚到指定版本
docker-compose exec backend alembic downgrade <revision>
```

### Q3: 如何扩展服务器资源?

- **垂直扩展:** 增加CPU/内存,调整worker数量
- **水平扩展:** 使用负载均衡器 (Nginx/HAProxy) + 多个后端实例
- **数据库扩展:** 读写分离,主从复制

### Q4: CORS错误怎么解决?

检查 `backend/.env` 中的 `ALLOWED_ORIGINS` 配置是否包含前端域名。

---

## 📞 技术支持

如遇到部署问题,请提供以下信息:
- 操作系统版本
- Python版本
- 错误日志
- 相关配置文件

---

**最后更新:** 2025-11-18
**文档版本:** 1.0.0