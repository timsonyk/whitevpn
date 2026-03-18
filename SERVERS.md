# WhiteLis VPN - Серверная инфраструктура

## Серверы

### 1. Бот сервер (SERVER_IP)
- **Назначение:** Telegram бот
- **SSH:** `ssh root@SERVER_IP` (ключ на локальной машине)
- **Сервис:** `whitevpn-bot`
- **Путь:** `/opt/whitevpn`
- **База данных:** `/opt/whitevpn/data/whitevpn.db`

**Команды:**
```bash
# Статус бота
systemctl status whitevpn-bot

# Перезапуск
systemctl restart whitevpn-bot

# Логи
journalctl -u whitevpn-bot -f
```

### 2. API сервер (SERVER_IP)
- **Назначение:** FastAPI для раздачи VPN конфигов
- **SSH:** `sshpass -p 'SERVER_PASSWORD' ssh root@SERVER_IP`
- **Логин:** root
- **Пароль:** `SERVER_PASSWORD`
- **Сервис:** `whitevpn-api`
- **Путь:** `/opt/whitevpn`
- **URL:** https://SERVER-IP.sslip.io
- **SSL:** Caddy (автоматический Let's Encrypt)

**Команды:**
```bash
# Статус API
systemctl status whitevpn-api

# Перезапуск
systemctl restart whitevpn-api

# Логи
journalctl -u whitevpn-api -f

# Caddy статус
systemctl status caddy
```

## Ссылки

- **API Docs:** https://SERVER-IP.sslip.io/docs
- **Конфиг URL:** `https://SERVER-IP.sslip.io/config/{token}`
- **Telegram бот:** @whitelisvpn_bot
- **Поддержка:** @WhiteLisVPN

## Деплой

### Обновить код на бот сервере:
```bash
rsync -avz -e "ssh" --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' --exclude '.env' --exclude 'venv' --exclude 'data' --exclude '.claude' /Users/timofey/Projects/whitevpn/ root@SERVER_IP:/opt/whitevpn/

ssh root@SERVER_IP 'systemctl restart whitevpn-bot'
```

### Обновить код на API сервере:
```bash
sshpass -p 'SERVER_PASSWORD' rsync -avz -e "ssh -o StrictHostKeyChecking=no" --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' --exclude '.env' --exclude 'venv' --exclude 'data' --exclude '.claude' /Users/timofey/Projects/whitevpn/ root@SERVER_IP:/opt/whitevpn/

sshpass -p 'SERVER_PASSWORD' ssh root@SERVER_IP 'systemctl restart whitevpn-api'
```

## Конфигурация

### .env (оба сервера)
```
BOT_TOKEN=TELEGRAM_BOT_TOKEN
API_HOST=0.0.0.0
API_PORT=8000
BASE_URL=https://SERVER-IP.sslip.io
SUBSCRIPTION_PRICE_STARS=189
SUBSCRIPTION_DAYS=30
CONFIG_URL=https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt
DATABASE_PATH=./data/whitevpn.db
```

## Админ

- **Telegram ID:** 389481960
- **Команда статистики:** `/stats` (только для админа)
