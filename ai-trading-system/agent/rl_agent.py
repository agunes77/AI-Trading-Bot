import os
import numpy as np
import pandas as pd
from stable_baselines3 import PPO, DQN, A2C
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from agent.environment import TradingEnvironment
from utils.logger import logger
from config.settings import RL_CONFIG, MODELS_DIR


class TrainingLogger(BaseCallback):
    def __init__(self, print_freq: int = 10):
        super().__init__()
        self.print_freq = print_freq

    def _on_step(self) -> bool:
        if self.n_calls % self.print_freq == 0:
            ep_rews = self.locals.get("ep_rewards", [])
            if ep_rews:
                logger.info(f"Step {self.n_calls} | Ortalama Odul: {np.mean(ep_rews):.4f}")
        return True


class RLAgent:
    def __init__(self, algorithm: str = None):
        self.algorithm = (algorithm or RL_CONFIG["algorithm"]).upper()
        self.model = None
        self.env = None
        self.feature_columns = []

    def _create_env(self, df: pd.DataFrame, feature_columns: list, initial_balance: float = 10000.0):
        self.feature_columns = feature_columns
        env = TradingEnvironment(df=df, feature_columns=feature_columns, initial_balance=initial_balance)
        env = Monitor(env)
        self.env = DummyVecEnv([lambda: env])
        return self.env

    def _get_model_class(self):
        mapping = {"PPO": PPO, "DQN": DQN, "A2C": A2C}
        cls = mapping.get(self.algorithm)
        if cls is None:
            logger.warning(f"{self.algorithm} desteklenmiyor, PPO'ya geciliyor")
            cls = PPO
            self.algorithm = "PPO"
        return cls

    def train(
        self,
        df: pd.DataFrame,
        feature_columns: list,
        total_timesteps: int = None,
        initial_balance: float = 10000.0,
        eval_df: pd.DataFrame = None,
    ):
        total_timesteps = total_timesteps or RL_CONFIG["total_timesteps"]
        self._create_env(df, feature_columns, initial_balance)

        model_cls = self._get_model_class()
        model_params = {
            "learning_rate": RL_CONFIG["learning_rate"],
            "gamma": RL_CONFIG["gamma"],
            "verbose": 0,
        }
        if self.algorithm == "PPO":
            model_params["n_steps"] = min(RL_CONFIG["n_steps"], len(df) - 1)
            model_params["batch_size"] = RL_CONFIG["batch_size"]
        elif self.algorithm == "DQN":
            model_params["batch_size"] = RL_CONFIG["batch_size"]
            model_params["learning_starts"] = 1000

        self.model = model_cls("MlpPolicy", self.env, **model_params)

        callbacks = [TrainingLogger(print_freq=500)]
        if eval_df is not None:
            eval_env = TradingEnvironment(df=eval_df, feature_columns=feature_columns, initial_balance=initial_balance)
            eval_env = Monitor(eval_env)
            eval_vec_env = DummyVecEnv([lambda: eval_env])
            callbacks.append(EvalCallback(
                eval_vec_env, best_model_save_path=str(MODELS_DIR / "best"),
                n_eval_episodes=5, eval_freq=max(total_timesteps // 10, 1000),
                deterministic=True,
            ))

        logger.info(f"Egitim basliyor | Algoritma: {self.algorithm} | Adim: {total_timesteps}")
        self.model.learn(total_timesteps=total_timesteps, callback=callbacks)
        logger.info("Egitim tamamlandi")
        return self.model

    def predict(self, observation: np.ndarray, deterministic: bool = True) -> int:
        if self.model is None:
            raise RuntimeError("Model egitilmemis veya yuklenmemis")
        action, _ = self.model.predict(observation, deterministic=deterministic)
        return int(action)

    def save(self, path: str = None):
        path = path or RL_CONFIG["model_path"]
        if self.model is None:
            logger.error("Kaydedilecek model yok")
            return
        self.model.save(path)
        logger.info(f"Model kaydedildi: {path}")

    def load(self, path: str = None):
        path = path or RL_CONFIG["model_path"]
        model_cls = self._get_model_class()
        if not os.path.exists(path + ".zip") and not os.path.exists(path):
            logger.error(f"Model dosyasi bulunamadi: {path}")
            return False
        self.model = model_cls.load(path)
        logger.info(f"Model yuklendi: {path}")
        return True

    def backtest(self, df: pd.DataFrame, feature_columns: list, initial_balance: float = 10000.0) -> dict:
        if self.model is None:
            raise RuntimeError("Model yuklu degil")
        env = TradingEnvironment(df=df, feature_columns=feature_columns, initial_balance=initial_balance)
        obs, _ = env.reset()
        done = False
        while not done:
            action = self.predict(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        return env.get_performance()
