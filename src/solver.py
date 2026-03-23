"""Решатель дифференциальных уравнений с запаздыванием"""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from typing import Tuple
import logging

from .config import ModelConfig

logger = logging.getLogger(__name__)


class DDESolver:
    """
    Решатель ДУЗ с использованием scipy.integrate.solve_ivp
    Метод: RK45 с адаптивным шагом
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self._history_func = None

    def solve(self, tau: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Решение ДУЗ: dx/dt = -λ·x(t) + μ·x(t-τ) - α·x(t)·x(t-τ)

        Args:
            tau: Запаздывание в часах

        Returns:
            t: Массив времени
            x: Массив состояния системы
        """
        t_span = (0, self.config.t_span_hours)
        t_eval = np.linspace(*t_span, self.config.n_points)

        # История для t < 0
        self._history_func = interp1d(
            [0], [self.config.x0],
            fill_value=self.config.x0,
            bounds_error=False
        )

        def dde_system(t, x):
            x_tau = self._get_history(t - tau)
            dx_dt = (
                    -self.config.lambda_f * x[0] +
                    self.config.mu_r * x_tau -
                    self.config.alpha * x[0] * x_tau
            )
            return [dx_dt]

        try:
            solution = solve_ivp(
                dde_system,
                t_span,
                [self.config.x0],
                t_eval=t_eval,
                method='RK45',
                rtol=1e-6,
                atol=1e-9,
                vectorized=False
            )

            if not solution.success:
                logger.warning(f"Решатель предупредил: {solution.message}")

            # Обновление истории
            self._history_func = interp1d(
                solution.t, solution.y[0],
                fill_value=self.config.x0,
                bounds_error=False
            )

            return solution.t, solution.y[0]

        except Exception as e:
            logger.error(f"Ошибка решения ДУЗ: {e}")
            raise

    def _get_history(self, t: float) -> float:
        """Получение значения из истории"""
        if self._history_func is None:
            return self.config.x0
        return float(self._history_func(t))