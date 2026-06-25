import numpy as np
import pandas as pd
from typing import Optional
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from utils.logger import logger
from config.settings import MODELS_DIR

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("xgboost yuklu degil")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("lightgbm yuklu degil")

try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    logger.warning("catboost yuklu degil")


class EnsembleML:
    def __init__(self, use_xgboost: bool = True, use_lightgbm: bool = True, use_catboost: bool = True):
        self.use_xgboost = use_xgboost and XGBOOST_AVAILABLE
        self.use_lightgbm = use_lightgbm and LIGHTGBM_AVAILABLE
        self.use_catboost = use_catboost and CATBOOST_AVAILABLE

        self.xgb_model = None
        self.lgb_model = None
        self.cat_model = None

        self.weights = {"xgboost": 0.4, "lightgbm": 0.35, "catboost": 0.25}
        self.feature_importance = {}
        self.is_trained = False

        logger.info(f"Ensemble ML baslatildi | XGB: {self.use_xgboost} | LGBM: {self.use_lightgbm} | CatBoost: {self.use_catboost}")

    def prepare_labels(self, df: pd.DataFrame, lookahead: int = 5, threshold: float = 0.005) -> pd.Series:
        future_returns = df["close"].shift(-lookahead) / df["close"] - 1
        labels = pd.Series(0, index=df.index)
        labels[future_returns > threshold] = 1
        labels[future_returns < -threshold] = -1
        return labels

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        n_estimators: int = 500,
    ) -> dict:
        y_train_binary = (y_train > 0).astype(int)
        if y_val is not None:
            y_val_binary = (y_val > 0).astype(int)
        else:
            y_val_binary = None

        results = {}

        if self.use_xgboost:
            logger.info("XGBoost egitimi basliyor...")
            self.xgb_model = xgb.XGBClassifier(
                n_estimators=n_estimators,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                objective="binary:logistic",
                eval_metric="logloss",
                use_label_encoder=False,
                random_state=42,
                n_jobs=-1,
            )
            self.xgb_model.fit(
                X_train, y_train_binary,
                eval_set=[(X_val, y_val_binary)] if X_val is not None else None,
                verbose=False,
            )
            self.feature_importance["xgboost"] = dict(zip(X_train.columns, self.xgb_model.feature_importances_))
            results["xgboost"] = self._evaluate_model(self.xgb_model, X_val, y_val_binary) if X_val is not None else {}
            logger.info(f"XGBoost egitimi tamamlandi")

        if self.use_lightgbm:
            logger.info("LightGBM egitimi basliyor...")
            self.lgb_model = lgb.LGBMClassifier(
                n_estimators=n_estimators,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                objective="binary",
                random_state=42,
                n_jobs=-1,
                verbose=-1,
            )
            self.lgb_model.fit(
                X_train, y_train_binary,
                eval_set=[(X_val, y_val_binary)] if X_val is not None else None,
            )
            self.feature_importance["lightgbm"] = dict(zip(X_train.columns, self.lgb_model.feature_importances_))
            results["lightgbm"] = self._evaluate_model(self.lgb_model, X_val, y_val_binary) if X_val is not None else {}
            logger.info(f"LightGBM egitimi tamamlandi")

        if self.use_catboost:
            logger.info("CatBoost egitimi basliyor...")
            self.cat_model = CatBoostClassifier(
                iterations=n_estimators,
                depth=6,
                learning_rate=0.05,
                l2_leaf_reg=3,
                random_seed=42,
                verbose=0,
                auto_class_weights="Balanced",
            )
            self.cat_model.fit(
                X_train, y_train_binary,
                eval_set=(X_val, y_val_binary) if X_val is not None else None,
                early_stopping_rounds=50 if X_val is not None else None,
            )
            self.feature_importance["catboost"] = dict(zip(X_train.columns, self.cat_model.get_feature_importance()))
            results["catboost"] = self._evaluate_model(self.cat_model, X_val, y_val_binary) if X_val is not None else {}
            logger.info(f"CatBoost egitimi tamamlandi")

        self.is_trained = True
        self._optimize_weights(X_val, y_val_binary)
        return results

    def _evaluate_model(self, model, X_val, y_val) -> dict:
        if X_val is None or y_val is None:
            return {}
        y_pred = model.predict(X_val)
        return {
            "accuracy": accuracy_score(y_val, y_pred),
            "precision": precision_score(y_val, y_pred, zero_division=0),
            "recall": recall_score(y_val, y_pred, zero_division=0),
            "f1": f1_score(y_val, y_pred, zero_division=0),
        }

    def _optimize_weights(self, X_val, y_val):
        if X_val is None or y_val is None:
            return

        preds = {}
        if self.xgb_model is not None:
            preds["xgboost"] = self.xgb_model.predict_proba(X_val)[:, 1]
        if self.lgb_model is not None:
            preds["lightgbm"] = self.lgb_model.predict_proba(X_val)[:, 1]
        if self.cat_model is not None:
            preds["catboost"] = self.cat_model.predict_proba(X_val)[:, 1]

        if len(preds) < 2:
            return

        best_score = 0
        best_weights = self.weights.copy()

        for w_xgb in np.arange(0.1, 0.9, 0.1):
            for w_lgb in np.arange(0.1, 0.9 - w_xgb, 0.1):
                w_cat = round(1.0 - w_xgb - w_lgb, 2)
                if w_cat < 0.05:
                    continue

                ensemble_pred = np.zeros(len(X_val))
                count = 0
                if "xgboost" in preds:
                    ensemble_pred += w_xgb * preds["xgboost"]
                    count += w_xgb
                if "lightgbm" in preds:
                    ensemble_pred += w_lgb * preds["lightgbm"]
                    count += w_lgb
                if "catboost" in preds:
                    ensemble_pred += w_cat * preds["catboost"]
                    count += w_cat

                if count > 0:
                    ensemble_pred /= count

                ensemble_binary = (ensemble_pred > 0.5).astype(int)
                score = accuracy_score(y_val, ensemble_binary)

                if score > best_score:
                    best_score = score
                    best_weights = {
                        "xgboost": w_xgb if "xgboost" in preds else 0,
                        "lightgbm": w_lgb if "lightgbm" in preds else 0,
                        "catboost": w_cat if "catboost" in preds else 0,
                    }

        self.weights = best_weights
        logger.info(f"Optimize agirliklar: {best_weights} | En iyi skor: {best_score:.4f}")

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Model egitilmemis")

        preds = {}
        total_weight = 0

        if self.xgb_model is not None:
            preds["xgboost"] = self.xgb_model.predict_proba(X)[:, 1]
            total_weight += self.weights.get("xgboost", 0)

        if self.lgb_model is not None:
            preds["lightgbm"] = self.lgb_model.predict_proba(X)[:, 1]
            total_weight += self.weights.get("lightgbm", 0)

        if self.cat_model is not None:
            preds["catboost"] = self.cat_model.predict_proba(X)[:, 1]
            total_weight += self.weights.get("catboost", 0)

        if not preds:
            raise RuntimeError("Hicbir model egitilmemis")

        ensemble_pred = np.zeros(len(X))
        for name, pred in preds.items():
            weight = self.weights.get(name, 0)
            ensemble_pred += weight * pred

        if total_weight > 0:
            ensemble_pred /= total_weight

        return ensemble_pred

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        proba = self.predict_proba(X)
        return (proba > 0.5).astype(int)

    def predict_signal(self, X: pd.DataFrame) -> np.ndarray:
        proba = self.predict_proba(X)
        signals = np.zeros(len(X))
        signals[proba > 0.6] = 1
        signals[proba < 0.4] = -1
        return signals

    def get_top_features(self, n: int = 20) -> dict:
        combined = {}
        for model_name, importance in self.feature_importance.items():
            weight = self.weights.get(model_name, 0)
            for feature, score in importance.items():
                if feature not in combined:
                    combined[feature] = 0
                combined[feature] += score * weight

        sorted_features = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_features[:n])

    def cross_validate(self, X: pd.DataFrame, y: pd.Series, n_splits: int = 5) -> dict:
        tscv = TimeSeriesSplit(n_splits=n_splits)
        cv_results = {
            "xgboost": [], "lightgbm": [], "catboost": [], "ensemble": []
        }

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            y_train_binary = (y_train > 0).astype(int)
            y_val_binary = (y_val > 0).astype(int)

            fold_preds = {}

            if self.use_xgboost:
                model = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42, n_jobs=-1, use_label_encoder=False, eval_metric="logloss")
                model.fit(X_train, y_train_binary, verbose=False)
                pred = model.predict(X_val)
                cv_results["xgboost"].append(accuracy_score(y_val_binary, pred))
                fold_preds["xgboost"] = model.predict_proba(X_val)[:, 1]

            if self.use_lightgbm:
                model = lgb.LGBMClassifier(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42, n_jobs=-1, verbose=-1)
                model.fit(X_train, y_train_binary)
                pred = model.predict(X_val)
                cv_results["lightgbm"].append(accuracy_score(y_val_binary, pred))
                fold_preds["lightgbm"] = model.predict_proba(X_val)[:, 1]

            if self.use_catboost:
                model = CatBoostClassifier(iterations=200, depth=6, learning_rate=0.05, random_seed=42, verbose=0)
                model.fit(X_train, y_train_binary)
                pred = model.predict(X_val)
                cv_results["catboost"].append(accuracy_score(y_val_binary, pred))
                fold_preds["catboost"] = model.predict_proba(X_val)[:, 1]

            if fold_preds:
                ensemble_pred = np.zeros(len(X_val))
                for name, pred in fold_preds.items():
                    ensemble_pred += self.weights.get(name, 0.33) * pred
                ensemble_binary = (ensemble_pred > 0.5).astype(int)
                cv_results["ensemble"].append(accuracy_score(y_val_binary, ensemble_binary))

        summary = {}
        for model_name, scores in cv_results.items():
            if scores:
                summary[model_name] = {
                    "mean": np.mean(scores),
                    "std": np.std(scores),
                    "scores": scores,
                }

        return summary
