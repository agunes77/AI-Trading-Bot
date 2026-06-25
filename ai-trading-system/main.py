import argparse
import time
import schedule
from pathlib import Path
from utils.logger import logger
from data.data_manager import DataManager
from features.technical_indicators import FeatureEngineer
from agent.rl_agent import RLAgent
from backtesting.backtester import Backtester
from backtesting.strategy_backtester import StrategyBacktester
from strategies.classic_strategies import ALL_STRATEGIES
from execution.risk_manager import RiskManager
from execution.crypto_executor import CryptoExecutor
from execution.forex_executor import ForexExecutor
from config.settings import BINANCE_CONFIG, MT5_CONFIG


def cmd_backtest(args):
    logger.info("=== BACKTEST MODU ===")
    dm = DataManager()
    fe = FeatureEngineer()
    agent = RLAgent(algorithm=args.algorithm)

    if args.source == "crypto":
        symbols = args.symbols.split(",") if args.symbols else BINANCE_CONFIG["symbols"]
        for symbol in symbols:
            logger.info(f"Backtest: {symbol}")
            df = dm.get_crypto_data(symbol, timeframe=args.timeframe, days=args.days)
            if df.empty:
                logger.error(f"Veri yok: {symbol}")
                continue
            bt = Backtester(agent=agent, feature_engineer=fe)
            results = bt.run(df, symbol=symbol)
            agent.save(str(Path("models") / f"bt_{symbol.replace('/', '_')}"))
    elif args.source == "forex":
        symbols = args.symbols.split(",") if args.symbols else MT5_CONFIG["symbols"]
        for symbol in symbols:
            logger.info(f"Backtest: {symbol}")
            df = dm.get_forex_data(symbol, timeframe=args.timeframe, days=args.days)
            if df.empty:
                logger.error(f"Veri yok: {symbol}")
                continue
            bt = Backtester(agent=agent, feature_engineer=fe)
            results = bt.run(df, symbol=symbol)
            agent.save(str(Path("models") / f"bt_{symbol}"))


def cmd_strategies(args):
    logger.info("=== STRATEJI ANALIZ MODU ===")
    dm = DataManager()

    if args.source == "crypto":
        symbol = args.symbol or BINANCE_CONFIG["symbols"][0]
        df = dm.get_crypto_data(symbol, timeframe=args.timeframe, days=args.days)
    else:
        symbol = args.symbol or MT5_CONFIG["symbols"][0]
        df = dm.get_forex_data(symbol, timeframe=args.timeframe, days=args.days)

    if df.empty:
        logger.error(f"Veri yok: {symbol}")
        return

    sb = StrategyBacktester()

    if args.mode == "compare":
        sb.run_comparison(df, symbol=symbol, stop_loss=args.stop_loss, take_profit=args.take_profit)
    elif args.mode == "top":
        sb.run_top_strategies(df, symbol=symbol, top_n=args.top_n, sort_by=args.sort_by)
    elif args.mode == "single":
        if not args.strategy:
            logger.error("--strategy parametresi gerekli. Mevcut: " + ", ".join(ALL_STRATEGIES.keys()))
            return
        sb.run_single(df, args.strategy, symbol=symbol, stop_loss=args.stop_loss, take_profit=args.take_profit)
    elif args.mode == "ensemble":
        sb.run_ensemble(df, symbol=symbol, stop_loss=args.stop_loss, take_profit=args.take_profit)
    elif args.mode == "list":
        logger.info(f"\nMevcut Stratejiler ({len(ALL_STRATEGIES)}):")
        logger.info("-" * 50)
        for key, cls in ALL_STRATEGIES.items():
            s = cls()
            logger.info(f"  {key:<20} {s.describe()}")


def cmd_ensemble(args):
    logger.info("=== ENSEMBLE ML BACKTEST MODU ===")
    dm = DataManager()

    if args.source == "crypto":
        symbol = args.symbol or BINANCE_CONFIG["symbols"][0]
        df = dm.get_crypto_data(symbol, timeframe=args.timeframe, days=args.days)
    else:
        symbol = args.symbol or MT5_CONFIG["symbols"][0]
        df = dm.get_forex_data(symbol, timeframe=args.timeframe, days=args.days)

    if df.empty:
        logger.error(f"Veri yok: {symbol}")
        return

    from ensemble.ensemble_backtester import EnsembleBacktester
    eb = EnsembleBacktester()
    result = eb.run(
        df, symbol=symbol,
        initial_balance=args.initial_balance,
        lookahead=args.lookahead,
        threshold=args.threshold,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
    )

    if "error" not in result:
        logger.info(f"\nEnsemble backtest tamamlandi: {symbol}")


def cmd_news(args):
    logger.info("=== HABER FILTRESI MODU ===")

    from news.news_filter import NewsFilter
    nf = NewsFilter()

    if args.mode == "check":
        can_trade, reason = nf.should_trade(symbol=args.symbol)
        if can_trade:
            logger.info("Trade yapilabilir: Haber filtresi engeli yok")
        else:
            logger.warning(f"Trade ENGELLENDI: {reason}")

    elif args.mode == "sentiment":
        condition = nf.get_market_condition(symbol=args.symbol)
        logger.info(f"\nPiyasa Kosulu: {condition['market_condition'].upper()}")
        logger.info(f"Toplam Skor: {condition['overall_score']:.1f}")
        logger.info(f"\nEkonomik Takvim:")
        cal = condition["calendar"]
        logger.info(f"  Yuksek Etkili Etkinlik: {cal['high_impact_count']}")
        logger.info(f"  Orta Etkili Etkinlik: {cal['medium_impact_count']}")
        logger.info(f"  Risk Seviyesi: {cal['risk_level']}")
        logger.info(f"\nHaber Sentimenti:")
        news = condition["news"]
        logger.info(f"  Ortalama Sentiment: {news['average_sentiment']:.2f}")
        logger.info(f"  Pozitif Haber: {news['positive_count']}")
        logger.info(f"  Negatif Haber: {news['negative_count']}")
        logger.info(f"  Piyasa Havasi: {news['market_mood']}")

    elif args.mode == "events":
        currencies = args.currencies.split(",") if args.currencies else None
        events = nf.get_upcoming_events(hours_ahead=args.hours, currencies=currencies)
        logger.info(f"\nYaklasan Yuksek Etkili Etkinlikler (sonraki {args.hours} saat):")
        logger.info("-" * 80)
        if not events:
            logger.info("  Yaklasan yuksek etkili etkinlik yok")
        for e in events:
            logger.info(f"  {e['time'][:16]} | {e['currency']:<4} | {e['event']}")

    elif args.mode == "headlines":
        news = nf.get_latest_news(limit=args.limit)
        logger.info(f"\nSon {len(news)} Haber:")
        logger.info("-" * 80)
        for n in news:
            sentiment_str = f"{n['sentiment']:+.2f}"
            impact = " [YUKSEK]" if n["high_impact"] else ""
            logger.info(f"  [{sentiment_str}] {n['title']}{impact}")
            logger.info(f"         Kaynak: {n['source']} | {n['time'][:16]}")


def cmd_risk(args):
    logger.info("=== RISK YONETIMI MODU ===")

    risk = RiskManager()

    if args.mode == "status":
        status = risk.get_status()
        logger.info(f"\nRisk Durumu:")
        logger.info("-" * 50)
        logger.info(f"  Acik Pozisyonlar: {status['open_trades']}/{status['max_open_trades']}")
        logger.info(f"  Gunluk PnL: ${status['daily_pnl']:.2f}")
        logger.info(f"  Haftalik PnL: ${status['weekly_pnl']:.2f}")
        logger.info(f"  Gunluk Kayip Limiti: {status['max_daily_loss_pct']:.1%}")
        logger.info(f"  Haftalik Kayip Limiti: {status['max_weekly_loss_pct']:.1%}")
        logger.info(f"  Max Korelasyon: {status['max_correlation']:.2f}")
        logger.info(f"  Art Arda Kayip: {status['consecutive_losses']}")
        logger.info(f"  Toplam Islem: {status['total_trades']}")
        logger.info(f"  Kazanma Orani: {status['win_rate']:.1f}%")

    elif args.mode == "report":
        report = risk.get_risk_report()
        logger.info(f"\nDetayli Risk Raporu:")
        logger.info("=" * 60)
        for key, value in report.items():
            if isinstance(value, float):
                logger.info(f"  {key:<25}: {value:.4f}")
            else:
                logger.info(f"  {key:<25}: {value}")
        logger.info("=" * 60)


def cmd_train(args):
    logger.info("=== EGITIM MODU ===")
    dm = DataManager()
    fe = FeatureEngineer()
    agent = RLAgent(algorithm=args.algorithm)

    symbol = args.symbol
    if args.source == "crypto":
        df = dm.get_crypto_data(symbol, timeframe=args.timeframe, days=args.days)
    else:
        df = dm.get_forex_data(symbol, timeframe=args.timeframe, days=args.days)

    if df.empty:
        logger.error(f"Veri yok: {symbol}")
        return

    df_features = fe.add_all_indicators(df)
    feature_cols = [c for c in fe.get_feature_columns() if c in df_features.columns]
    df_clean = df_features.dropna(subset=feature_cols)

    split = int(len(df_clean) * 0.8)
    train_df = df_clean.iloc[:split]
    eval_df = df_clean.iloc[split:]

    agent.train(
        df=train_df,
        feature_columns=feature_cols,
        total_timesteps=args.timesteps,
        eval_df=eval_df,
    )
    agent.save(args.output or str(Path("models") / f"agent_{symbol.replace('/', '_')}"))
    logger.info("Egitim tamamlandi ve model kaydedildi")


def cmd_live(args):
    logger.info("=== CANLI TRADE MODU ===")
    risk = RiskManager()
    agent = RLAgent()

    model_path = args.model or str(Path("models") / "trading_agent")
    if not agent.load(model_path):
        logger.error("Model yuklenemedi. Once 'train' veya 'backtest' komutunu calistirin.")
        return

    enable_news_filter = not args.no_news_filter
    if enable_news_filter:
        from news.news_filter import NewsFilter
        news_filter = NewsFilter()
        can_trade, reason = news_filter.should_trade()
        if not can_trade:
            logger.error(f"Haber filtresi trade'i engelledi: {reason}")
            logger.info("Haber filtresini devre disi birakmak icin --no-news-filter kullanin")
            return
        logger.info("Haber filtresi kontrolu gecildi")

    if args.source == "crypto":
        executor = CryptoExecutor(agent=agent, risk_manager=risk)
        symbols = args.symbols.split(",") if args.symbols else BINANCE_CONFIG["symbols"]
        interval_minutes = _tf_to_minutes(args.timeframe or BINANCE_CONFIG["default_timeframe"])
        logger.info(f"Kripto canli trade basliyor: {symbols} | Aralik: {interval_minutes}dk")
        _run_live_loop(executor, symbols, interval_minutes, source="crypto")
    elif args.source == "forex":
        executor = ForexExecutor(agent=agent, risk_manager=risk)
        if not executor.connect():
            logger.error("MT5 baglantisi basarisiz")
            return
        symbols = args.symbols.split(",") if args.symbols else MT5_CONFIG["symbols"]
        interval_minutes = _tf_to_minutes(args.timeframe or MT5_CONFIG["default_timeframe"])
        logger.info(f"Forex canli trade basliyor: {symbols} | Aralik: {interval_minutes}dk")
        try:
            _run_live_loop(executor, symbols, interval_minutes, source="forex")
        finally:
            executor.disconnect()


def _run_live_loop(executor, symbols, interval_minutes, source="crypto"):
    def job():
        for symbol in symbols:
            try:
                executor.run_cycle(symbol)
            except Exception as e:
                logger.error(f"Hata {symbol}: {e}")

    logger.info(f"Canli trade dongusu basladi. Her {interval_minutes} dakikada calisacak.")
    logger.info("Durdurmak icin Ctrl+C basin.")
    job()
    schedule.every(interval_minutes).minutes.do(job)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Canli trade durduruldu.")


def _tf_to_minutes(tf: str) -> int:
    mapping = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440,
               "M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
    return mapping.get(tf, 60)


def cmd_data(args):
    logger.info("=== VERI YONETIMI MODU ===")
    from data.dukascopy_downloader import DataManager, DukascopyDownloader
    
    dm = DataManager()
    
    if args.mode == "download":
        logger.info(f"Veri indiriliyor: {args.instrument} ({args.start_date} - {args.end_date})")
        df = dm.fetch_data(
            source=args.source,
            instrument=args.instrument,
            start_date=args.start_date,
            end_date=args.end_date,
            timeframe=args.timeframe
        )
        if df is not None:
            logger.info(f"Veri indirildi: {len(df)} satir")
        else:
            logger.error("Veri indirilemedi")
    
    elif args.mode == "list":
        data = dm.list_all_data()
        logger.info("\nIndirilmis Veriler:")
        logger.info("-" * 80)
        for source, files in data.items():
            logger.info(f"\n{source.upper()}:")
            for f in files:
                logger.info(f"  {f['filename']} - {f['size_mb']:.2f} MB - {f['created']}")
    
    elif args.mode == "delete":
        if dm.delete_data(args.source, args.filename):
            logger.info(f"Veri silindi: {args.filename}")
        else:
            logger.error("Silme islemi basarisiz")
    
    elif args.mode == "instruments":
        downloader = DukascopyDownloader()
        instruments = downloader.get_available_instruments()
        logger.info(f"\nDukascopy Mevcut Enstrumanlar ({len(instruments)}):")
        logger.info("-" * 80)
        for inst in instruments[:50]:
            logger.info(f"  {inst}")
        if len(instruments) > 50:
            logger.info(f"  ... ve {len(instruments) - 50} daha")


def cmd_trading_agents(args):
    logger.info("=== TRADINGAGENTS LLM MODU ===")
    
    try:
        from agent.trading_agents_llm import TradingAgentsLLM, TRADING_AGENTS_AVAILABLE
        
        if not TRADING_AGENTS_AVAILABLE:
            logger.error("tradingagents paketi yuklu degil. pip install tradingagents")
            return
        
        if args.mode == "analyze":
            config = {
                "llm_provider": args.llm_provider,
                "max_debate_rounds": args.max_debate_rounds,
            }
            
            if args.deep_think_model:
                config["deep_think_llm"] = args.deep_think_model
            if args.quick_think_model:
                config["quick_think_llm"] = args.quick_think_model
            
            llm = TradingAgentsLLM(config=config)
            result = llm.analyze(args.ticker, args.date)
            
            logger.info(f"\nAnaliz Sonucu: {result['ticker']} @ {result['date']}")
            logger.info("-" * 80)
            logger.info(f"Karar: {result['decision']}")
            
            if result.get('state'):
                logger.info("\nDetayli Analiz:")
                for key, value in result['state'].items():
                    logger.info(f"\n{key.replace('_', ' ').title()}:")
                    logger.info(f"  {value}")
        
        elif args.mode == "status":
            logger.info(f"TradingAgents Durumu: {'Hazir' if TRADING_AGENTS_AVAILABLE else 'Degil'}")
    
    except ImportError as e:
        logger.error(f"Import hatasi: {e}")
    except Exception as e:
        logger.error(f"Hata: {e}")


def main():
    parser = argparse.ArgumentParser(description="AI Destekli Trade Sistemi")
    subparsers = parser.add_subparsers(dest="command", help="Komut secin")

    bt_parser = subparsers.add_parser("backtest", help="RL agent ile backtest")
    bt_parser.add_argument("--source", choices=["crypto", "forex"], default="crypto")
    bt_parser.add_argument("--symbols", type=str, default=None)
    bt_parser.add_argument("--timeframe", type=str, default=None)
    bt_parser.add_argument("--days", type=int, default=365)
    bt_parser.add_argument("--algorithm", choices=["PPO", "DQN", "A2C"], default="PPO")
    bt_parser.set_defaults(func=cmd_backtest)

    strat_parser = subparsers.add_parser("strategies", help="Klasik stratejileri analiz et")
    strat_parser.add_argument("--mode", choices=["compare", "top", "single", "ensemble", "list"], default="compare",
                              help="compare: tum stratejileri karsilastir, top: en iyileri bul, single: tek strateji, ensemble: toplu sinyal, list: stratejileri listele")
    strat_parser.add_argument("--source", choices=["crypto", "forex"], default="crypto")
    strat_parser.add_argument("--symbol", type=str, default=None)
    strat_parser.add_argument("--strategy", type=str, default=None, help="Tek strateji testi icin strateji adi")
    strat_parser.add_argument("--timeframe", type=str, default=None)
    strat_parser.add_argument("--days", type=int, default=365)
    strat_parser.add_argument("--top_n", type=int, default=5)
    strat_parser.add_argument("--sort_by", choices=["sharpe_ratio", "total_return_pct", "max_drawdown_pct", "win_rate_pct", "profit_factor"], default="sharpe_ratio")
    strat_parser.add_argument("--stop_loss", type=float, default=0.02)
    strat_parser.add_argument("--take_profit", type=float, default=0.04)
    strat_parser.set_defaults(func=cmd_strategies)

    ensemble_parser = subparsers.add_parser("ensemble", help="Ensemble ML (XGBoost+LightGBM+CatBoost) backtest")
    ensemble_parser.add_argument("--source", choices=["crypto", "forex"], default="crypto")
    ensemble_parser.add_argument("--symbol", type=str, default=None)
    ensemble_parser.add_argument("--timeframe", type=str, default=None)
    ensemble_parser.add_argument("--days", type=int, default=365)
    ensemble_parser.add_argument("--initial_balance", type=float, default=10000.0)
    ensemble_parser.add_argument("--lookahead", type=int, default=5, help="Kac mum ileriye bakilacak")
    ensemble_parser.add_argument("--threshold", type=float, default=0.005, help="Etiket esik degeri")
    ensemble_parser.add_argument("--stop_loss", type=float, default=0.02)
    ensemble_parser.add_argument("--take_profit", type=float, default=0.04)
    ensemble_parser.set_defaults(func=cmd_ensemble)

    news_parser = subparsers.add_parser("news", help="Haber filtresi ve sentiment analizi")
    news_parser.add_argument("--mode", choices=["check", "sentiment", "events", "headlines"], default="sentiment",
                             help="check: trade edilebilir mi, sentiment: piyasa kosulu, events: ekonomik takvim, headlines: son haberler")
    news_parser.add_argument("--symbol", type=str, default=None, help="Sembol (para birimi otomatik cikarilir)")
    news_parser.add_argument("--currencies", type=str, default=None, help="Para birimleri (ORN: USD,EUR)")
    news_parser.add_argument("--hours", type=int, default=24, help="Ileriye bakilacak saat")
    news_parser.add_argument("--limit", type=int, default=10, help="Gosterilecek haber sayisi")
    news_parser.set_defaults(func=cmd_news)

    risk_parser = subparsers.add_parser("risk", help="Risk yonetimi durumu ve rapor")
    risk_parser.add_argument("--mode", choices=["status", "report"], default="status",
                             help="status: anlik durum, report: detayli rapor")
    risk_parser.set_defaults(func=cmd_risk)

    train_parser = subparsers.add_parser("train", help="RL agent egit")
    train_parser.add_argument("--source", choices=["crypto", "forex"], default="crypto")
    train_parser.add_argument("--symbol", type=str, required=True)
    train_parser.add_argument("--timeframe", type=str, default=None)
    train_parser.add_argument("--days", type=int, default=365)
    train_parser.add_argument("--timesteps", type=int, default=100000)
    train_parser.add_argument("--algorithm", choices=["PPO", "DQN", "A2C"], default="PPO")
    train_parser.add_argument("--output", type=str, default=None)
    train_parser.set_defaults(func=cmd_train)

    live_parser = subparsers.add_parser("live", help="Canli trade baslat")
    live_parser.add_argument("--source", choices=["crypto", "forex"], default="crypto")
    live_parser.add_argument("--symbols", type=str, default=None)
    live_parser.add_argument("--timeframe", type=str, default=None)
    live_parser.add_argument("--model", type=str, default=None)
    live_parser.add_argument("--no-news-filter", action="store_true", help="Haber filtresini devre disi birak")
    live_parser.set_defaults(func=cmd_live)

    data_parser = subparsers.add_parser("data", help="Veri yonetimi (indirme, listeleme, silme)")
    data_parser.add_argument("--mode", choices=["download", "list", "delete", "instruments"], default="list",
                             help="download: veri indir, list: indirilenleri listele, delete: veri sil, instruments: mevcut enstrumanlari listele")
    data_parser.add_argument("--source", choices=["dukascopy", "binance", "mt5"], default="dukascopy")
    data_parser.add_argument("--instrument", type=str, default="EURUSD", help="Enstruman (EURUSD, BTCUSD, AAPL...)")
    data_parser.add_argument("--start_date", type=str, default="2024-01-01", help="Baslangic tarihi (YYYY-MM-DD)")
    data_parser.add_argument("--end_date", type=str, default="2024-12-31", help="Bitis tarihi (YYYY-MM-DD)")
    data_parser.add_argument("--timeframe", choices=["tick", "minutely", "hourly", "daily"], default="hourly")
    data_parser.add_argument("--filename", type=str, help="Silinecek dosya adi")
    data_parser.set_defaults(func=cmd_data)

    ta_parser = subparsers.add_parser("trading-agents", help="TradingAgents LLM multi-agent analiz")
    ta_parser.add_argument("--mode", choices=["analyze", "status"], default="status",
                           help="analyze: LLM analizi yap, status: durum kontrolu")
    ta_parser.add_argument("--ticker", type=str, default="AAPL", help="Sembol (AAPL, BTC-USD, EURUSD...)")
    ta_parser.add_argument("--date", type=str, default=None, help="Analiz tarihi (YYYY-MM-DD)")
    ta_parser.add_argument("--llm_provider", choices=["openai", "anthropic", "google", "deepseek", "ollama"], default="openai")
    ta_parser.add_argument("--deep_think_model", type=str, default=None, help="Derin dusunme modeli")
    ta_parser.add_argument("--quick_think_model", type=str, default=None, help="Hizli dusunme modeli")
    ta_parser.add_argument("--max_debate_rounds", type=int, default=2, help="Maksimum tartisma turu")
    ta_parser.set_defaults(func=cmd_trading_agents)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
