"""Расчёт метрик отказоустойчивости"""
import numpy as np
from typing import Dict
from dataclasses import dataclass


@dataclass
class MetricsResult:
    """Результаты расчёта метрик"""
    K_g: float
    P_fail: float
    T_first_failure: float
    x_mean: float
    x_min: float
    x_max: float


def calculate_metrics(
        t: np.ndarray,
        x: np.ndarray,
        theta_threshold: float = 0.9,
        theta_critical: float = 0.5
) -> MetricsResult:
    """
    Расчёт метрик работоспособности

    Args:
        t: Массив времени (часы)
        x: Массив состояния системы
        theta_threshold: Порог готовности
        theta_critical: Критический порог

    Returns:
        MetricsResult с рассчитанными метриками
    """
    indicator_working = (x >= theta_threshold).astype(float)
    indicator_failed = (x < theta_critical).astype(float)

    time_span = t[-1] - t[0]
    if time_span <= 0:
        time_span = 1.0

    K_g = np.trapezoid(indicator_working, t) / time_span * 100.0
    P_fail = np.trapezoid(indicator_failed, t) / time_span * 100.0

    failure_indices = np.where(x < theta_critical)[0]
    if len(failure_indices) > 0:
        T_first_failure = t[failure_indices[0]] * 60.0
    else:
        T_first_failure = t[-1] * 60.0

    return MetricsResult(
        K_g=K_g,
        P_fail=P_fail,
        T_first_failure=T_first_failure,
        x_mean=float(np.mean(x)),
        x_min=float(np.min(x)),
        x_max=float(np.max(x))
    )


def critical_delay(lambda_f: float, mu_r: float) -> float:
    """Расчёт критического запаздывания"""
    if mu_r <= lambda_f:
        return float('inf')
    return np.arccos(lambda_f / mu_r) / np.sqrt(mu_r ** 2 - lambda_f ** 2)


def stability_margin(tau_crit: float, tau: float) -> float:
    """Расчёт запаса устойчивости в %"""
    if tau_crit == float('inf') or tau_crit == 0:
        return 0.0
    return max(0.0, (tau_crit - tau) / tau_crit * 100.0)