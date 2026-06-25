# AI Trading System

🚀 **Gelişmiş AI destekli otomatik ticaret sistemi** - Kripto ve Forex piyasaları için çoklu strateji, RL agent ve LLM tabanlı karar verme

## ✨ Özellikler

### 🤖 AI & Machine Learning
- **Reinforcement Learning (RL)** - PPO, DQN, A2C algoritmaları ile otomatik strateji öğrenimi
- **Ensemble ML** - XGBoost + LightGBM + CatBoost birleşimi
- **TradingAgents LLM** - 9 özel agent ile çoklu LLM karar motoru (OpenAI, Anthropic, Google, DeepSeek)
- **Pine Script Entegrasyonu** - TradingView indikatörlerini Python'a dönüştürme

### 📊 Strateji Geliştirme
- **Görsel Strateji Editörü** - Sürükle-bırak node-based arayüz (BloodHound tarzı)
- **Pine Script Kod Editörü** - Monaco editor ile TradingView uyumlu kod yazma
- **23+ Hazır Strateji** - RSI, MACD, Bollinger, Ichimoku, Supertrend vb.
- **10+ Pine Script Preset** - RSI+MACD, BB Breakout, EMA Cross vb.

### 📈 Teknik Analiz
- **60+ İndikatör** - SMA, EMA, RSI, MACD, Bollinger, ATR, Stochastic, Ichimoku, Supertrend, PSAR, Pivot, Fibonacci vb.
- **Özel İndikatörler** - DEMA, TEMA, HMA, AO, KST, TRIX, Connors RSI vb.

### 🛡️ Risk Yönetimi
- **Günlük/Haftalık Kayıp Limitleri**
- **Korelasyon Kontrolü** - Benzer varlıklarda aynı anda pozisyon engelleme
- **Dinamik Pozisyon Boyutlandırma** - Volatilite bazlı otomatik ayarlama
- **ATR Bazlı Stop-Loss/Take-Profit**

### 📰 Haber Filtresi
- **Ekonomik Takvim** - Yüksek etkili etkinliklerde otomatik trade durdurma
- **Sentiment Analizi** - Kripto haberlerinden piyasa havası tespiti
- **Otomatik Trade Engelleme** - Negatif sentiment veya yüksek etkili haber öncesi

### 💾 Veri Yönetimi
- **Dukascopy Entegrasyonu** - 1000+ enstrüman, 1990'dan bugüne tick verisi
- **Binance & MT5** - Kripto ve Forex veri çekme
- **Parquet Cache** - Hızlı veri erişimi

### 🌐 Web Arayüzü
- **Dashboard** - Portföy özeti, PnL, varlık dağılımı
- **Canlı Fiyatlar** - WebSocket ile gerçek zamanlı veri
- **Grafik & Analiz** - TradingView benzeri grafikler
- **Strateji Performans** - Backtest sonuçları ve karşılaştırma
- **AI Model Eğitimi** - RL agent eğitimi ve yönetimi

## 🏗️ Mimari

```
ai-trading-system/
├── agent/                  # RL agent ve TradingAgents LLM
├── backtesting/           # Backtest motorları
├── broker/                # Broker entegrasyonları (Binance, MT5)
├── config/                # Konfigürasyon dosyaları
├── data/                  # Veri çekme ve yönetimi
├── ensemble/              # Ensemble ML (XGB+LGB+Cat)
├── execution/             # Trade çalıştırma ve risk yönetimi
├── features/              # Teknik indikatörler
├── news/                  # Haber filtresi ve sentiment
├── pine_script/           # Pine Script parser ve runner
├── strategies/            # Hazır stratejiler
├── strategy_builder/      # Görsel strateji editörü
├── utils/                 # Yardımcı fonksiyonlar
└── web/                   # Web arayüzü (FastAPI + React)
```

## 🚀 Kurulum

### Gereksinimler
- Python 3.11+
- Node.js 20+
- Docker (opsiyonel)

### 1. Projeyi Klonla
```bash
git clone https://github.com/kullanici-adi/ai-trading-system.git
cd ai-trading-system
```

### 2. Python Bağımlılıkları
```bash
pip install -r requirements.txt
```

### 3. Ortam Değişkenleri
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

### 4. Frontend Build
```bash
cd web/frontend
npm install
npm run build
cd ../..
```

### 5. Çalıştır
```bash
# Backend
python web/backend/run.py

# Frontend (geliştirme)
cd web/frontend
npm run dev
```

Uygulama adresleri:
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000

## 🐳 Docker ile Kurulum

```bash
# .env dosyasını düzenleyin
cp .env.example .env
nano .env

# Docker Compose ile başlatın
docker-compose up -d

# Logları görüntüleyin
docker-compose logs -f
```

## 📖 Kullanım

### CLI Komutları

```bash
# RL Agent Eğitimi
python main.py train --source crypto --symbol BTC/USDT --timesteps 100000

# Ensemble ML Backtest
python main.py ensemble --source crypto --symbol BTC/USDT --days 365

# Strateji Karşılaştırma
python main.py strategies --mode compare --source crypto --symbol ETH/USDT

# TradingAgents LLM Analizi
python main.py trading-agents --mode analyze --ticker AAPL --llm_provider openai

# Haber Filtresi Kontrolü
python main.py news --mode check --symbol EURUSD

# Risk Durumu
python main.py risk --mode status

# Veri İndirme (Dukascopy)
python main.py data --mode download --source dukascopy --instrument EURUSD --start_date 2024-01-01 --end_date 2024-12-31

# Canlı Trade
python main.py live --source crypto --symbols BTC/USDT,ETH/USDT
```

### Web Arayüzü

Tarayıcınızda `http://localhost:3000` adresine gidin:

1. **Dashboard** - Portföy özeti ve piyasa durumu
2. **Canlı Fiyatlar** - Gerçek zamanlı fiyat takibi
3. **Grafik & Analiz** - Teknik analiz grafikleri
4. **Stratejiler** - 23+ hazır strateji backtest
5. **Strateji Tasarımcısı** - Görsel editör + Pine Script
6. **Veri Yönetimi** - Dukascopy veri indirme
7. **TradingAgents LLM** - Multi-agent analiz
8. **Trade Geçmişi** - İşlem kayıtları
9. **AI Model Eğitimi** - RL agent yönetimi

## 🔧 Konfigürasyon

### .env Dosyası
```bash
# Binance API
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_SANDBOX=true

# MetaTrader 5
MT5_LOGIN=12345
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Demo

# LLM API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Risk Yönetimi
RISK_MAX_POSITION_PCT=0.02
RISK_MAX_DAILY_LOSS_PCT=0.05
RISK_MAX_WEEKLY_LOSS_PCT=0.10
RISK_MAX_OPEN_TRADES=3
RISK_MAX_CORRELATION=0.7
```

## 📊 Strateji Örnekleri

### Görsel Editör ile Strateji Oluşturma
1. Strateji Tasarımcısı sayfasına gidin
2. Sol panelden node'ları sürükleyin
3. Bağlantıları kurun
4. "Çalıştır" ile backtest yapın

### Pine Script ile Strateji Yazma
```pine
//@version=5
indicator("EMA Cross", overlay=true)
fast = ta.ema(close, 9)
slow = ta.ema(close, 21)
bullish = ta.crossover(fast, slow)
bearish = ta.crossunder(fast, slow)
plot(fast, "Fast", color=blue)
plot(slow, "Slow", color=red)
```

## 🌍 OVH Dokploy ile Deploy

Detaylı talimatlar için [DEPLOYMENT.md](DEPLOYMENT.md) dosyasına bakın.

```bash
# Sunucuya yükleyin
scp -r ai-trading-system root@your-server:/opt/

# Docker Compose ile deploy
docker-compose up -d --build
```

## 📝 Lisans

Bu proje eğitim ve araştırma amaçlıdır. Gerçek para ile trade yapmadan önce kapsamlı test yapın.

## ⚠️ Sorumluluk Reddi

**Bu yazılım sadece eğitim ve araştırma amaçlıdır.** Finansal tavsiye değildir. Ticaret risk içerir ve para kaybına neden olabilir. Past performance gelecek sonuçların garantisi değildir.

## 🤝 Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır. Büyük değişiklikler için önce issue açın.

## 📧 İletişim

Sorularınız için issue açın veya pull request gönderin.

---

**Not:** Bu sistem sürekli geliştirilmektedir. En güncel özellikler için commit geçmişine bakın.
