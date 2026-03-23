"""Решатель для многокомпонентной модели Kubernetes"""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class MultiComponentDDESolver:
    """
    Система ДУЗ для моделирования Kubernetes
    Компоненты: [Control Plane, Worker Nodes, Pods]
    """

    def __init__(self, params: Dict, tau: float):
        """
        Args:
            params: Словарь параметров модели
            tau: Запаздывание в часах
        """
        self.params = params
        self.tau = tau
        self._history_funcs = None  # Список интерполяторов для каждого компонента
        self.n_components = 3  # C, W, P
        self.y0 = np.array([
            params.get('C0', 1.0),
            params.get('W0', 1.0),
            params.get('P0', 1.0)
        ])

    def _rhs(self, t: float, y: np.ndarray, y_tau: np.ndarray) -> np.ndarray:
        """
        Система уравнений:

        dC/dt = -λ_c·C(t) + μ_c·C(t-τ) - α_cc·C(t)·C(t-τ) - α_cp·C(t)·P(t-τ)
        dW/dt = -λ_w·W(t) + μ_w·W(t-τ) - α_ww·W(t)·W(t-τ) - α_wp·W(t)·P(t-τ)
        dP/dt = -λ_p·P(t) + μ_p·P(t-τ) - α_pp·P(t)·P(t-τ) + β_c·C(t-τ) + β_w·W(t-τ)
        """
        C, W, P = y
        C_tau, W_tau, P_tau = y_tau

        p = self.params

        dC_dt = (
                -p['lambda_c'] * C +
                p['mu_c'] * C_tau -
                p['alpha_cc'] * C * C_tau -
                p['alpha_cp'] * C * P_tau
        )

        dW_dt = (
                -p['lambda_w'] * W +
                p['mu_w'] * W_tau -
                p['alpha_ww'] * W * W_tau -
                p['alpha_wp'] * W * P_tau
        )

        dP_dt = (
                -p['lambda_p'] * P +
                p['mu_p'] * P_tau -
                p['alpha_pp'] * P * P_tau +
                p['beta_c'] * C_tau +
                p['beta_w'] * W_tau
        )

        return np.array([dC_dt, dW_dt, dP_dt])

    def _get_history(self, t: float) -> np.ndarray:
        """Получение значения из истории для каждого компонента"""
        if t >= 0 and self._history_funcs is not None:
            return np.array([func(t) for func in self._history_funcs])
        # Возврат начальных условий для t < 0
        return self.y0.copy()

    def solve(self, t_span: Tuple[float, float],
              y0: np.ndarray = None,
              n_points: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Решение системы ДУЗ

        Returns:
            t: Массив времени (часы)
            y: Массив состояния (time × components)
        """
        if y0 is None:
            y0 = self.y0.copy()

        t_eval = np.linspace(*t_span, n_points)

        # Инициализация истории для каждого компонента отдельно
        # FIX: Создаём отдельный интерполятор для каждого компонента
        self._history_funcs = [
            interp1d([0], [y0[i]], fill_value=y0[i], bounds_error=False)
            for i in range(self.n_components)
        ]

        def dde_system(t, y):
            y_tau = self._get_history(t - self.tau)
            return self._rhs(t, y, y_tau)

        try:
            solution = solve_ivp(
                dde_system,
                t_span,
                y0,
                t_eval=t_eval,
                method='RK45',
                rtol=1e-6,
                atol=1e-9
            )

            if not solution.success:
                logger.warning(f"Решатель предупредил: {solution.message}")

            # FIX: Обновляем историю для каждого компонента отдельно
            self._history_funcs = [
                interp1d(
                    solution.t,
                    solution.y[i],
                    fill_value=y0[i],
                    bounds_error=False
                )
                for i in range(self.n_components)
            ]

            # Возврат: t (n_points,), y (n_points, 3)
            return solution.t, solution.y.T

        except Exception as e:
            logger.error(f"Ошибка решения многокомпонентного ДУЗ: {e}")
            raise