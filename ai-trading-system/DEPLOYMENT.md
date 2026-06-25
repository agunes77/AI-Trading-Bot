# AI Trading System - OVH Dokploy Deployment

## Ön Hazırlık

### 1. OVH Sunucuya Bağlanın
```bash
ssh root@your-server-ip
```

### 2. Dokploy'un Kurulu Olduğundan Emin Olun
```bash
dokploy --version
```

### 3. Projeyi Sunucuya Yükleyin

**Yöntem 1: Git ile**
```bash
cd /opt
git clone https://github.com/your-repo/ai-trading-system.git
cd ai-trading-system
```

**Yöntem 2: SCP ile**
```bash
# Yerel makineden
scp -r ai-trading-system root@your-server-ip:/opt/
```

## Dokploy ile Deploy

### Yöntem 1: Docker Compose (Önerilen)

1. **Dokploy Dashboard'a Gidin**
   ```
   http://your-server-ip:3000
   ```

2. **Yeni Uygulama Oluşturun**
   - "Create Service" → "Docker Compose"
   - Name: `ai-trading-system`
   - Upload `docker-compose.yml` dosyasını

3. **Environment Variables Ekleyin**
   Dokploy dashboard'dan:
   ```
   BINANCE_API_KEY=your_key
   BINANCE_API_SECRET=your_secret
   OPENAI_API_KEY=your_key
   ```

4. **Deploy Edin**
   - "Deploy" butonuna tıklayın
   - Build sürecini izleyin

### Yöntem 2: CLI ile Deploy

```bash
cd /opt/ai-trading-system

# .env dosyasını oluşturun
cp .env.example .env
nano .env  # API anahtarlarınızı girin

# Docker Compose ile deploy
docker-compose up -d --build

# Logları kontrol edin
docker-compose logs -f
```

## Domain Yapılandırması (Opsiyonel)

### Dokploy Dashboard ile Domain Ekleyin

1. **Backend için Domain**
   - Service: `ai-trading-backend`
   - Domain: `api.yourdomain.com`
   - SSL: Let's Encrypt (otomatik)

2. **Frontend için Domain**
   - Service: `ai-trading-frontend`
   - Domain: `yourdomain.com`
   - SSL: Let's Encrypt (otomatik)

### Manuel Nginx Reverse Proxy

```bash
# Nginx kurun
apt update
apt install nginx

# Backend için
nano /etc/nginx/sites-available/api.yourdomain.com
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Frontend için
nano /etc/nginx/sites-available/yourdomain.com
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
# Siteleri aktif edin
ln -s /etc/nginx/sites-available/api.yourdomain.com /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/yourdomain.com /etc/nginx/sites-enabled/

# SSL sertifikası alın
apt install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Nginx'i yeniden başlatın
systemctl reload nginx
```

## Kontrol

### Servis Durumu
```bash
docker-compose ps
```

### Loglar
```bash
# Tüm loglar
docker-compose logs -f

# Backend logları
docker-compose logs -f backend

# Frontend logları
docker-compose logs -f frontend
```

### Erişim Testi
```bash
# Backend health check
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

## Güncelleme

```bash
cd /opt/ai-trading-system

# Kodu güncelleyin
git pull

# Yeniden deploy
docker-compose up -d --build

# Eski image'ları temizleyin
docker image prune -f
```

## Sorun Giderme

### Container Başlamıyor
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Port Çakışması
```bash
# Kullanılan portları kontrol edin
netstat -tulpn | grep -E '8000|3000'

# docker-compose.yml'den portları değiştirin
```

### Bellek Yetersiz
```bash
# Docker limitlerini ayarlayın
nano docker-compose.yml
```

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Veri Kalıcılığı
```bash
# Volume'leri kontrol edin
docker volume ls

# Yedekleme
tar -czvf backup-$(date +%Y%m%d).tar.gz models/ logs/ data_cache/
```

## Güvenlik

### Firewall Ayarları
```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### API Anahtarları
- `.env` dosyasını asla Git'e commit etmeyin
- Dokploy dashboard'dan environment variable olarak ekleyin
- Production'da `BINANCE_SANDBOX=false` yapın

### SSL Zorunluluğu
```nginx
# Nginx config'e ekleyin
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Performans İzleme

```bash
# Container kaynak kullanımı
docker stats

# Disk kullanımı
df -h

# Bellek kullanımı
free -h
```

## Yedekleme

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/ai-trading"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Veritabanı yedekleme (varsa)
# docker-compose exec db pg_dump ...

# Model ve log yedekleme
tar -czvf $BACKUP_DIR/backup-$DATE.tar.gz \
    models/ \
    logs/ \
    data_cache/ \
    .env

# 30 günden eski yedekleri sil
find $BACKUP_DIR -name "backup-*.tar.gz" -mtime +30 -delete

echo "Backup completed: backup-$DATE.tar.gz"
```

```bash
# Cron job ekleyin
crontab -e
0 2 * * * /path/to/backup.sh
```

## Destek

Sorun yaşarsanız:
1. Logları kontrol edin: `docker-compose logs -f`
2. Dokploy dashboard'dan service status'a bakın
3. Container'ları yeniden başlatın: `docker-compose restart`

Başarılar! 🚀
