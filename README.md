# 星星存折 (Star Savings) - Python版本

面向3-10岁儿童的家庭奖励系统,通过星星积分激励良好行为。

**本项目是原[`tbphp/star`](https://github.com/tbphp/star)后端的Python FastAPI完整移植版本,实现100%功能对等。**

## 技术栈

### 后端 (Python)
- **FastAPI 0.115+** - 现代异步Web框架
- **SQLAlchemy 2.0** - 异步ORM
- **Pydantic V2** - 数据验证和序列化
- **aiosqlite** - 异步SQLite驱动
- **Alembic** - 数据库迁移工具
- **Uvicorn** - ASGI服务器

### 前端 (复用原项目)
- Vue 3.5.18
- Vite 7.0
- TypeScript
- Tailwind CSS 4.0
- Anime.js 4.2.2

### 部署
- Docker + Docker Compose
- Nginx (反向代理)

## 核心功能

- ✅ 小朋友管理(添加、编辑、查看、删除)
- ✅ 星星加减操作 + 可爱动画
- ✅ 星星记录查看(最近20条)
- ✅ 奖品创建(支持绑定多个小朋友)
- ✅ 奖品进度展示(星星堆叠)
- ✅ 灵活兑换(可编辑扣除分配)
- ✅ 兑换动画(烟花+翻转)
- ✅ 响应式适配(iPad/手机)

## 快速开始

### 方式1: Docker Compose部署(暂时有bug，不建议)

```bash
# 1. 确保安装Docker和Docker Compose

# 2. 构建前端(如果还没有dist目录)
cd star/frontend
npm install
npm run build

# 3. 复制前端构建产物到新项目
cp -r star/frontend/dist newpro/frontend/

# 4. 启动服务
cd newpro
docker-compose up -d

# 5. 查看日志
docker-compose logs -f

# 6. 访问应用
# 前端: http://localhost:8008
# 后端API文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/health
```

**首次启动说明:**
- 后端容器启动时会自动运行数据库迁移创建表结构
- SQLite数据库文件位于: `backend/storage/app/database.sqlite`
- 上传的头像和奖品图片存储在: `backend/storage/app/public/`

### 方式2: 本地开发

#### 后端开发

```bash
cd newpro/backend

# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件,配置数据库路径等

# 4. 运行数据库迁移
alembic upgrade head

# 5. 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API文档访问: http://localhost:8000/docs
```

#### 前端开发(复用原项目)

```bash
cd star/frontend

# 1. 安装依赖
npm install

# 2. 配置API地址
# 编辑 src/api/index.ts 确保baseURL指向Python后端

# 3. 启动开发服务器
npm run dev

# 访问: http://localhost:5173
```

### 方式3: 本地开发(小型服务器环境安装困难时可以参考)

#### 后端开发
在 CentOS 7（低配、老旧内核）上部署 Python 3.11 遇到的核心挑战与解决方案：
```
# 1. 下载兼容 glibc 2.17 的 Python 3.11 包
cd ~
wget https://github.com/indygreg/python-build-standalone/releases/download/20240726/cpython-3.11.9+20240726-x86_64-unknown-linux-gnu-install_only.tar.gz

# 2. 解压并安装到 /usr/local
tar -xzf cpython-3.11.9+20240726-x86_64-unknown-linux-gnu-install_only.tar.gz
sudo mv python /usr/local/python3.11
sudo chmod -R 755 /usr/local/python3.11

# 3. 创建系统软链接 (如有旧版 python3 请先备份)
sudo ln -sf /usr/local/python3.11/bin/python3 /usr/bin/python3
sudo ln -sf /usr/local/python3.11/bin/pip3 /usr/bin/pip3

# 4. 验证
python3 --version  # 应输出 Python 3.11.9
```

```
cd /opt/git/starpy

# 使用清华源加速安装
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

```
创建服务文件以实现开机自启和后台管理。
sudo vi /etc/systemd/system/starpy.service
写入以下内容：
code
Ini
[Unit]
Description=Starpy Backend Service
After=network.target

[Service]
Type=simple
# 项目根目录
WorkingDirectory=/opt/git/starpy
# 启动命令
ExecStart=/usr/bin/python3 main.py
# 环境变量：禁用缓冲区以便查看日志
Environment=PYTHONUNBUFFERED=1
# 生产环境建议关闭 Debug (需配合代码修改)
# Environment=APP_ENV=production

# 自动重启策略
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
启动后端服务：
code
Bash
sudo systemctl daemon-reload
sudo systemctl start starpy
sudo systemctl enable starpy
```


```bash

# 配置环境变量
cp .env.example .env
# 编辑.env文件,配置数据库路径等

# API文档访问: http://localhost:8000/docs
```

#### 前端开发(复用原项目)
##### 安装 Nginx

```
# 安装 EPEL 源
yum install -y epel-release
# 安装 Nginx
yum install -y nginx
# 启动 Nginx
systemctl start nginx
systemctl enable nginx
```
##### 上传前端文件
将打包好的前端资源（dist 文件夹内的内容）上传到服务器。
假设路径为：/opt/git/starpy/frontend/dist

##### 配置 Nginx 反向代理
编辑配置文件：
sudo vi /etc/nginx/conf.d/starpy.conf
```
server {
    listen 38000;
    # 将此处替换为你的域名或服务器IP
    server_name _; 

    # 1. 前端静态资源托管
    location / {
        root /opt/git/starpy/frontend/dist;
        index index.html;
        # SPA 单页应用必备：路由找不到时回退到 index.html
        try_files $uri $uri/ /index.html;
    }

    # 2. 后端 API 反向代理
    # 假设后端接口都以 /api 开头，或者根据实际情况调整
    # 如果后端没有统一前缀，可能需要根据实际路由调整 location
    location /api/ { 
        proxy_pass http://127.0.0.1:38001;
        
        # 传递真实 IP 头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 支持 WebSocket (如果项目用了的话)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
##### 重载 Nginx
检查配置是否正确并重启：
```
nginx -t
systemctl reload nginx
```

## 项目结构

```
newpro/
├── backend/                    # Python FastAPI后端
│   ├── app/
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 环境配置
│   │   │   ├── database.py    # 数据库连接
│   │   │   ├── exceptions.py  # 自定义异常
│   │   │   └── response.py    # 统一响应格式
│   │   ├── models/            # SQLAlchemy模型
│   │   │   ├── child.py       # 小朋友模型
│   │   │   ├── reward.py      # 奖品模型
│   │   │   ├── star_record.py # 星星记录模型
│   │   │   └── reward_child.py # 关联表模型
│   │   ├── schemas/           # Pydantic验证模型
│   │   │   ├── child.py
│   │   │   ├── star.py
│   │   │   └── reward.py
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── base_service.py # 泛型基类服务
│   │   │   ├── child_service.py
│   │   │   ├── star_service.py
│   │   │   └── reward_service.py
│   │   ├── api/               # API路由
│   │   │   ├── deps.py        # 依赖注入
│   │   │   └── v1/
│   │   │       ├── children.py # 小朋友接口
│   │   │       ├── stars.py    # 星星操作接口
│   │   │       └── rewards.py  # 奖品接口
│   │   └── utils/             # 工具类
│   │       └── file_handler.py # 文件处理
│   ├── alembic/               # 数据库迁移
│   │   ├── versions/          # 迁移脚本
│   │   └── env.py
│   ├── storage/               # 存储目录
│   │   ├── app/
│   │   │   ├── public/        # 公开文件
│   │   │   └── database.sqlite # SQLite数据库
│   │   └── logs/
│   ├── main.py               # FastAPI应用入口
│   ├── requirements.txt      # Python依赖
│   ├── .env.example         # 环境变量模板
│   └── Dockerfile
├── frontend/                 # 前端构建产物(复用原项目)
│   └── dist/
├── docker-compose.yml       # Docker编排配置
├── nginx.conf              # Nginx配置
└── README.md

star/                        # 原Laravel项目(前端源码)
├── frontend/
│   ├── src/
│   └── package.json
└── backend/                 # 原PHP后端(参考)
```

## API接口文档

### Children资源(小朋友管理)

```
GET    /api/children           列出所有小朋友
GET    /api/children/{id}      获取小朋友详情(含记录+奖品)
POST   /api/children           创建小朋友(支持头像上传)
PUT    /api/children/{id}      更新小朋友信息
DELETE /api/children/{id}      删除小朋友(级联删除记录)
```

### Star操作(星星加减)

```
POST /api/children/{id}/stars/add       加星(1-50范围)
POST /api/children/{id}/stars/subtract  减星(余额验证)
```

### Rewards资源(奖品管理)

```
GET    /api/rewards            列出所有奖品(含进度)
POST   /api/rewards            创建奖品(需child_ids)
PUT    /api/rewards/{id}       更新奖品(已兑换禁止)
DELETE /api/rewards/{id}       删除奖品(已兑换禁止)
POST   /api/rewards/{id}/redeem 兑换奖品(复杂验证)
```

**完整API文档**: 启动服务后访问 http://localhost:8000/docs

## 数据库设计

### children表(小朋友)
```sql
id              INTEGER PRIMARY KEY
name            VARCHAR(50) NOT NULL
birthday        DATE NOT NULL
gender          VARCHAR(10) NOT NULL
avatar          VARCHAR(255)
star_count      INTEGER DEFAULT 0  -- 冗余字段,加速查询
created_at      DATETIME
updated_at      DATETIME

-- 计算属性: age (根据birthday计算)
```

### rewards表(奖品)
```sql
id              INTEGER PRIMARY KEY
name            VARCHAR(100) NOT NULL
image           VARCHAR(255)
star_cost  INTEGER NOT NULL
is_redeemed     BOOLEAN DEFAULT 0
redeemed_at     DATETIME
created_at      DATETIME
updated_at      DATETIME

-- 计算属性: total_stars (关联小朋友的星星总和)
-- 计算属性: is_achieved (total_stars >= star_cost)
```

### reward_children表(奖品-小朋友关联)
```sql
id                INTEGER PRIMARY KEY
reward_id         INTEGER NOT NULL REFERENCES rewards
child_id          INTEGER NOT NULL REFERENCES children
deduction_amount  INTEGER  -- 兑换时实际扣除的星星数
created_at        DATETIME

UNIQUE(reward_id, child_id)
```

### star_records表(星星记录)
```sql
id         INTEGER PRIMARY KEY
child_id   INTEGER NOT NULL REFERENCES children
type       VARCHAR(20) NOT NULL  -- 'add' | 'subtract' | 'redeem'
amount     INTEGER NOT NULL
reason     VARCHAR(255)
reward_id  INTEGER REFERENCES rewards  -- 兑换时关联奖品
created_at DATETIME

-- 复合索引: (child_id, created_at)  -- 查询最近记录
-- 索引: (child_id, type)            -- 统计不同类型操作
-- 索引: (reward_id)                 -- 查询兑换记录
```

## 开发说明

### 架构设计模式

1. **标准分层架构**: Models → Schemas → Services → Routers
2. **泛型基类服务**: `BaseService[ModelType]`提供通用CRUD
3. **依赖注入**: FastAPI的`Depends()`机制管理数据库会话
4. **统一响应**: 保持与Laravel API 100%兼容的响应格式
5. **异步优先**: 所有数据库操作使用`async/await`

### 事务处理

所有涉及星星变动的操作都使用事务保证数据一致性:
```python
async with db.begin():
    # 1. 插入star_records
    # 2. 更新children.star_count
    # 3. 更新reward状态(兑换时)
```

### 文件上传处理

- **支持格式**: JPG, JPEG, PNG, GIF, WEBP
- **大小限制**: 5MB
- **存储路径**: `storage/app/public/avatars/` 或 `rewards/`
- **访问URL**: `http://localhost:8008/storage/avatars/{filename}`
- **删除策略**: 更新头像时自动删除旧文件

### 兑换验证流程

1. 验证奖品存在且未兑换
2. 验证deductions中的child_ids都在奖品关联中
3. 验证总扣除数量等于star_cost
4. 验证每个小朋友的星星余额充足
5. 事务中执行扣除+记录+状态更新

## 常见问题

### 1. 数据库迁移失败

```bash
# 检查数据库文件权限
ls -l backend/storage/app/

# 重置迁移(警告:会清空数据)
cd backend
alembic downgrade base
alembic upgrade head
```

### 2. 文件上传失败

```bash
# 检查storage目录权限
chmod -R 755 backend/storage

# Docker环境检查挂载
docker-compose exec backend ls -la /app/storage/app/public/
```

### 3. CORS错误

编辑`backend/.env`:
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:8008
```

### 4. 前端API连接失败

检查前端API配置(`star/frontend/src/api/index.ts`):
```typescript
const baseURL = 'http://localhost:8000/api';
```

## 与原Laravel项目的差异

### 保持一致
- ✅ 数据库结构100%相同
- ✅ API接口路径和参数完全一致
- ✅ 响应格式相同
- ✅ 业务逻辑规则相同
- ✅ 前端代码无需修改

### 技术差异
- 🔄 PHP → Python
- 🔄 Laravel → FastAPI
- 🔄 Eloquent ORM → SQLAlchemy
- 🔄 同步IO → 异步IO
- 🔄 Composer → Pip

## 性能特点

- **异步IO**: 所有数据库操作异步化,提高并发性能
- **连接池**: SQLAlchemy连接池复用,减少连接开销
- **类型安全**: Pydantic严格类型验证,运行时错误更少
- **自动文档**: FastAPI自动生成OpenAPI文档

## 开发工具

```bash
# 代码格式化
pip install black
black backend/

# 类型检查
pip install mypy
mypy backend/

# 测试(如需添加)
pip install pytest pytest-asyncio
pytest backend/tests/
```

## 许可证

MIT

## 贡献指南

1. Fork本项目
2. 创建特性分支(`git checkout -b feature/AmazingFeature`)
3. 提交更改(`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支(`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 联系方式

如有问题或建议,请提交Issue或Pull Request。