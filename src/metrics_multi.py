"""Метрики для многокомпонентной модели"""
import numpy as np
from dataclasses import dataclass
from typing import Dict


@dataclass
class MultiComponentMetrics:
    """Метрики для каждого компонента"""
    # Control Plane
    K_g_C: float
    P_fail_C: float
    T_first_failure_C: float

    # Worker Nodes
    K_g_W: float
    P_fail_W: float
    T_first_failure_W: float

    # Pods
    K_g_P: float
    P_fail_P: float
    T_first_failure_P: float

    # Интегральные
    K_g_avg: float
    P_fail_avg: float
    T_first_failure_system: float


def calculate_multi_metrics(
        t: np.ndarray,
        y: np.ndarray,
        theta_threshold: float = 0.9,
        theta_critical: float = 0.5
) -> MultiComponentMetrics:
    """
    Расчёт метрик для многокомпонентной модели

    Args:
        t: Массив времени (часы)
        y: Массив состояния (time × 3 компонента)
        theta_threshold: Порог готовности
        theta_critical: Критический порог

    Returns:
        MultiComponentMetrics с рассчитанными метриками
    """
    C = y[:, 0]  # Control Plane
    W = y[:, 1]  # Worker Nodes
    P = y[:, 2]  # Pods

    time_span = t[-1] - t[0]
    if time_span <= 0:
        time_span = 1.0

    def calc_component_metrics(x: np.ndarray, name: str):
        indicator_working = (x >= theta_threshold).astype(float)
        indicator_failed = (x < theta_critical).astype(float)

        K_g = np.trapezoid(indicator_working, t) / time_span * 100.0
        P_fail = np.trapezoid(indicator_failed, t) / time_span * 100.0

        failure_indices = np.where(x < theta_critical)[0]
        T_first = t[failure_indices[0]] * 60.0 if len(failure_indices) > 0 else t[-1] * 60.0

        return K_g, P_fail, T_first

    K_g_C, P_fail_C, T_C = calc_component_metrics(C, 'C')
    K_g_W, P_fail_W, T_W = calc_component_metrics(W, 'W')
    K_g_P, P_fail_P, T_P = calc_component_metrics(P, 'P')

    # Интегральные метрики (система работает, если все компоненты работают)
    system_working = (C >= theta_threshold) & (W >= theta_threshold) & (P >= theta_threshold)
    system_failed = (C < theta_critical) | (W < theta_critical) | (P < theta_critical)

    K_g_avg = np.trapezoid(system_working.astype(float), t) / time_span * 100.0
    P_fail_avg = np.trapezoid(system_failed.astype(float), t) / time_span * 100.0

    # Время до первого отказа системы (минимум из всех компонентов)
    T_first_system = min(T_C, T_W, T_P)

    return MultiComponentMetrics(
        K_g_C=K_g_C, P_fail_C=P_fail_C, T_first_failure_C=T_C,
        K_g_W=K_g_W, P_fail_W=P_fail_W, T_first_failure_W=T_W,
        K_g_P=K_g_P, P_fail_P=P_fail_P, T_first_failure_P=T_P,
        K_g_avg=K_g_avg, P_fail_avg=P_fail_avg, T_first_failure_system=T_first_system
    )