import pandas as pd
from strategy_builder.solvers.base_solver import BaseSolver


class ComparisonSolver(BaseSolver):
    id = "comparison"
    name = "Comparison (A vs B)"
    category = "Confidence Solver"
    description = "İki değeri karşılaştırır (>, <, ==). Koşul sağlandığında 100, sağlanmadığında 0."
    inputs = [
        {"id": "value1", "name": "Değer A", "type": "series"},
        {"id": "value2", "name": "Değer B", "type": "series"}
    ]
    parameters = {"operator": ">"}  # ">", "<", ">=", "<=", "==", "!="

    def calculate(self, data: pd.DataFrame, inputs: Dict[str, Any]) -> pd.Series:
        v1 = inputs.get("value1", data["close"])
        v2 = inputs.get("value2", data["close"])
        op = self.params.get("operator", ">")

        if op == ">":
            res = v1 > v2
        elif op == "<":
            res = v1 < v2
        elif op == ">=":
            res = v1 >= v2
        elif op == "<=":
            res = v1 <= v2
        elif op == "==":
            res = (v1 == v2).astype(float) * 100
        elif op == "!=":
            res = v1 != v2
        else:
            res = pd.Series(False, index=data.index)

        return self._to_score(res).fillna(0)