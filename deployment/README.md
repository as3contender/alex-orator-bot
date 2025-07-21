# CloverdashBot - Развертывание

Инструкции по развертыванию CloverdashBot в различных окружениях.

## 🚀 Быстрый старт

### 1. Подготовка окружения

```bash
# Клонирование репозитория
git clone <your-repo> cloverdashbot
cd cloverdashbot

# Настройка проекта
make setup
```

### 2. Конфигурация

Отредактируйте файлы конфигурации:

#### Backend (.env)
```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Базы данных
APP_DATABASE_URL=postgresql://cloverdashbot:password@localhost:5432/app_db
DATA_DATABASE_URL=postgresql://cloverdashbot:password@localhost:5433/data_db

# Безопасность
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

#### Telegram Bot (.env)
```env
TELEGRAM_TOKEN=your_telegram_bot_token
BACKEND_URL=http://localhost:8000
```

### 3. Запуск

```bash
# Локальная разработка
make local-up

# Production
make production-up
```

## 🐳 Docker развертывание

### Локальная разработка

```bash
# Запуск всех сервисов
docker-compose -f docker-compose.local.yml up -d

# Просмотр логов
docker-compose -f docker-compose.local.yml logs -f

# Остановка
docker-compose -f docker-compose.local.yml down
```

### Production

```bash
# Запуск production окружения
docker-compose up -d

# С Nginx (production профиль)
docker-compose --profile production up -d
```

## ☸️ Kubernetes развертывание

### 1. Создание namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cloverdashbot
```

### 2. Создание ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cloverdashbot-config
  namespace: cloverdashbot
data:
  BACKEND_URL: "http://cloverdashbot-backend:8000"
  LOG_LEVEL: "INFO"
```

### 3. Создание Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cloverdashbot-secrets
  namespace: cloverdashbot
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-key>
  TELEGRAM_TOKEN: <base64-encoded-token>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
  SECRET_KEY: <base64-encoded-secret>
  APP_DB_PASSWORD: <base64-encoded-password>
  DATA_DB_PASSWORD: <base64-encoded-password>
```

### 4. Развертывание PostgreSQL

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: cloverdashbot-app-db
  namespace: cloverdashbot
spec:
  serviceName: cloverdashbot-app-db
  replicas: 1
  selector:
    matchLabels:
      app: cloverdashbot-app-db
  template:
    metadata:
      labels:
        app: cloverdashbot-app-db
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: "app_db"
        - name: POSTGRES_USER
          value: "cloverdashbot"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: cloverdashbot-secrets
              key: APP_DB_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: app-db-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: app-db-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

### 5. Развертывание Backend

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloverdashbot-backend
  namespace: cloverdashbot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cloverdashbot-backend
  template:
    metadata:
      labels:
        app: cloverdashbot-backend
    spec:
      containers:
      - name: backend
        image: cloverdashbot-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "false"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: cloverdashbot-secrets
              key: OPENAI_API_KEY
        - name: APP_DATABASE_URL
          value: "postgresql://cloverdashbot:$(APP_DB_PASSWORD)@cloverdashbot-app-db:5432/app_db"
        - name: DATA_DATABASE_URL
          value: "postgresql://cloverdashbot:$(DATA_DB_PASSWORD)@cloverdashbot-data-db:5432/data_db"
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: cloverdashbot-secrets
              key: JWT_SECRET_KEY
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: cloverdashbot-secrets
              key: SECRET_KEY
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 6. Развертывание Telegram Bot

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloverdashbot-telegram
  namespace: cloverdashbot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cloverdashbot-telegram
  template:
    metadata:
      labels:
        app: cloverdashbot-telegram
    spec:
      containers:
      - name: telegram-bot
        image: cloverdashbot-telegram:latest
        env:
        - name: TELEGRAM_TOKEN
          valueFrom:
            secretKeyRef:
              name: cloverdashbot-secrets
              key: TELEGRAM_TOKEN
        - name: BACKEND_URL
          valueFrom:
            configMapKeyRef:
              name: cloverdashbot-config
              key: BACKEND_URL
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: cloverdashbot-config
              key: LOG_LEVEL
```

### 7. Создание Services

```yaml
apiVersion: v1
kind: Service
metadata:
  name: cloverdashbot-backend
  namespace: cloverdashbot
spec:
  selector:
    app: cloverdashbot-backend
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: cloverdashbot-app-db
  namespace: cloverdashbot
spec:
  selector:
    app: cloverdashbot-app-db
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

### 8. Ingress (опционально)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cloverdashbot-ingress
  namespace: cloverdashbot
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.cloverdashbot.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cloverdashbot-backend
            port:
              number: 80
```

## 🔧 Настройка базы данных

### Инициализация схемы

```sql
-- Создание пользователя с ограниченными правами для данных
CREATE USER data_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE data_db TO data_user;
GRANT USAGE ON SCHEMA public TO data_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO data_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO data_user;

-- Настройка прав на будущие таблицы
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO data_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO data_user;
```

### Импорт данных

```bash
# Импорт данных в data_db
psql -h localhost -p 5433 -U cloverdashbot -d data_db -f your_data.sql

# Или через Docker
docker exec -i cloverdashbot-data-db psql -U cloverdashbot -d data_db < your_data.sql
```

## 📊 Мониторинг

### Prometheus метрики

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'cloverdashbot-backend'
      static_configs:
      - targets: ['cloverdashbot-backend:8000']
      metrics_path: /metrics
```

### Grafana дашборд

Создайте дашборд для мониторинга:
- Количество запросов
- Время ответа API
- Ошибки
- Использование ресурсов

## 🔒 Безопасность

### SSL/TLS сертификаты

```bash
# Генерация самоподписанного сертификата
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deployment/ssl/nginx.key \
  -out deployment/ssl/nginx.crt
```

### Firewall правила

```bash
# Ограничение доступа к базам данных
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 5432 -j DROP

iptables -A INPUT -p tcp --dport 5433 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 5433 -j DROP
```

## 🚀 CI/CD

### GitHub Actions

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build and push Docker images
      run: |
        docker build -t cloverdashbot-backend ./backend
        docker build -t cloverdashbot-telegram ./telegram-bot
        # Push to registry
    
    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f k8s/
        kubectl rollout restart deployment/cloverdashbot-backend
        kubectl rollout restart deployment/cloverdashbot-telegram
```

## 📝 Логирование

### Централизованное логирование

```yaml
# Fluentd конфигурация
<source>
  @type tail
  path /var/log/containers/cloverdashbot-*.log
  pos_file /var/log/cloverdashbot.log.pos
  tag cloverdashbot
  read_from_head true
  <parse>
    @type json
    time_key time
    time_format %Y-%m-%dT%H:%M:%S.%NZ
  </parse>
</source>

<match cloverdashbot>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name cloverdashbot
</match>
```

## 🔄 Обновления

### Rolling Update

```bash
# Обновление с нулевым временем простоя
kubectl set image deployment/cloverdashbot-backend backend=cloverdashbot-backend:v2.0.0
kubectl rollout status deployment/cloverdashbot-backend

kubectl set image deployment/cloverdashbot-telegram telegram-bot=cloverdashbot-telegram:v2.0.0
kubectl rollout status deployment/cloverdashbot-telegram
```

### Rollback

```bash
# Откат к предыдущей версии
kubectl rollout undo deployment/cloverdashbot-backend
kubectl rollout undo deployment/cloverdashbot-telegram
``` 