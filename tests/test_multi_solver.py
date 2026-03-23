#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты для многокомпонентной модели Kubernetes
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Добавляем корневую директорию проекта в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.solver_multi import MultiComponentDDESolver
from src.metrics_multi import calculate_multi_metrics, MultiComponentMetrics
from src.export import save_multi_to_csv


class TestMultiComponentDDESolver:
    """Тесты для решателя многокомпонентной модели"""

    @pytest.fixture
    def default_params(self):
        """Параметры по умолчанию для тестов"""
        return {
            'lambda_c': 0.10,
            'mu_c': 0.40,
            'alpha_cc': 0.05,
            'alpha_cp': 0.10,
            'lambda_w': 0.20,
            'mu_w': 0.35,
            'alpha_ww': 0.08,
            'alpha_wp': 0.12,
            'lambda_p': 0.30,
            'mu_p': 0.25,
            'alpha_pp': 0.15,
            'beta_c': 0.05,
            'beta_w': 0.10,
            'C0': 1.0,
            'W0': 1.0,
            'P0': 1.0
        }

    def test_solver_initialization(self, default_params):
        """Тест инициализации решателя"""
        tau = 0.001  # 3.6 секунды в часах
        solver = MultiComponentDDESolver(default_params, tau)

        assert solver.tau == tau
        assert solver.n_components == 3
        assert np.allclose(solver.y0, [1.0, 1.0, 1.0])

    def test_solve_returns_correct_shapes(self, default_params):
        """Тест корректности формы выходных данных"""
        solver = MultiComponentDDESolver(default_params, tau=0.001)
        t_span = (0, 10)  # 10 часов
        n_points = 1000

        t, y = solver.solve(t_span, n_points=n_points)

        assert len(t) == n_points
        assert y.shape == (n_points, 3)  # 3 компонента
        assert t[0] == 0.0
        assert t[-1] == 10.0

    def test_solution_bounded(self, default_params):
        """Тест ограниченности решения диапазоном [0, 1]"""
        solver = MultiComponentDDESolver(default_params, tau=0.001)
        t, y = solver.solve((0, 50), n_points=5000)

        # Все компоненты должны быть в диапазоне [0, 1]
        assert np.all(y >= -0.01), "Отрицательные значения в решении"
        assert np.all(y <= 1.01), "Значения больше 1 в решении"

    def test_initial_conditions_preserved(self, default_params):
        """Тест сохранения начальных условий"""
        # Устанавливаем нестандартные начальные условия
        default_params['C0'] = 0.8
        default_params['W0'] = 0.9
        default_params['P0'] = 1.0

        solver = MultiComponentDDESolver(default_params, tau=0.001)
        t, y = solver.solve((0, 1), n_points=100)

        # Проверяем начальные значения (с небольшой погрешностью)
        assert abs(y[0, 0] - 0.8) < 0.01, "Control Plane начальное условие"
        assert abs(y[0, 1] - 0.9) < 0.01, "Worker Nodes начальное условие"
        assert abs(y[0, 2] - 1.0) < 0.01, "Pods начальное условие"

    def test_different_tau_values(self, default_params):
        """Тест решения с разными значениями запаздывания"""
        tau_values = [0.0001, 0.001, 0.01]  # Разные запаздывания
        solutions = []

        for tau in tau_values:
            solver = MultiComponentDDESolver(default_params, tau)
            t, y = solver.solve((0, 10), n_points=1000)
            solutions.append(y)

        # Решения должны быть разными для разных tau
        for i in range(len(solutions) - 1):
            diff = np.abs(solutions[i] - solutions[i + 1]).max()
            assert diff > 1e-6, f"Решения для tau {tau_values[i]} и {tau_values[i + 1]} одинаковы"

    def test_rhs_function(self, default_params):
        """Тест функции правой части уравнений"""
        solver = MultiComponentDDESolver(default_params, tau=0.001)

        # Тестовые значения
        y = np.array([0.9, 0.8, 0.7])
        y_tau = np.array([1.0, 0.9, 0.8])

        dy_dt = solver._rhs(0, y, y_tau)

        assert len(dy_dt) == 3
        assert isinstance(dy_dt, np.ndarray)

    def test_history_function(self, default_params):
        """Тест функции истории"""
        solver = MultiComponentDDESolver(default_params, tau=0.001)

        # До решения история должна возвращать начальные условия
        history_before = solver._get_history(-1.0)
        assert np.allclose(history_before, [1.0, 1.0, 1.0])

        # Решаем систему
        solver.solve((0, 5), n_points=500)

        # После решения история должна работать
        history_after = solver._get_history(2.0)
        assert len(history_after) == 3


class TestMultiComponentMetrics:
    """Тесты для расчёта метрик многокомпонентной модели"""

    @pytest.fixture
    def sample_data(self):
        """Пример данных для тестов"""
        t = np.linspace(0, 100, 10000)

        # Создаём тестовые траектории
        C = 0.95 + 0.05 * np.sin(t / 10)  # Control Plane: 0.90-1.00
        W = 0.90 + 0.10 * np.sin(t / 15)  # Worker Nodes: 0.80-1.00
        P = 0.85 + 0.15 * np.sin(t / 20)  # Pods: 0.70-1.00

        y = np.column_stack([C, W, P])
        return t, y

    def test_metrics_calculation(self, sample_data):
        """Тест расчёта метрик"""
        t, y = sample_data
        metrics = calculate_multi_metrics(t, y, theta_threshold=0.9, theta_critical=0.5)

        assert isinstance(metrics, MultiComponentMetrics)
        assert 0 <= metrics.K_g_C <= 100
        assert 0 <= metrics.K_g_W <= 100
        assert 0 <= metrics.K_g_P <= 100
        assert 0 <= metrics.K_g_avg <= 100

    def test_metrics_for_perfect_system(self):
        """Тест метрик для идеальной системы"""
        t = np.linspace(0, 100, 1000)
        y = np.ones((1000, 3))  # Все компоненты всегда работают

        metrics = calculate_multi_metrics(t, y)

        assert metrics.K_g_C == 100.0
        assert metrics.K_g_W == 100.0
        assert metrics.K_g_P == 100.0
        assert metrics.K_g_avg == 100.0
        assert metrics.P_fail_C == 0.0
        assert metrics.P_fail_W == 0.0
        assert metrics.P_fail_P == 0.0

    def test_metrics_for_failed_system(self):
        """Тест метрик для полностью отказавшей системы"""
        t = np.linspace(0, 100, 1000)
        y = np.zeros((1000, 3))  # Все компоненты отказали

        metrics = calculate_multi_metrics(t, y)

        assert metrics.K_g_C == 0.0
        assert metrics.K_g_W == 0.0
        assert metrics.K_g_P == 0.0
        assert metrics.K_g_avg == 0.0
        assert metrics.P_fail_C == 100.0
        assert metrics.P_fail_W == 100.0
        assert metrics.P_fail_P == 100.0

    def test_first_failure_time(self):
        """Тест времени до первого отказа"""
        t = np.linspace(0, 100, 10000)

        # Control Plane отказывает на 30 часу
        C = np.ones_like(t)
        C[t >= 30] = 0.4

        # Worker Nodes отказывают на 50 часу
        W = np.ones_like(t)
        W[t >= 50] = 0.4

        # Pods всегда работают
        P = np.ones_like(t)

        y = np.column_stack([C, W, P])
        metrics = calculate_multi_metrics(t, y, theta_critical=0.5)

        # Первый отказ должен быть Control Plane на 30 часу = 1800 минут
        assert abs(metrics.T_first_failure_C - 1800) < 1
        assert abs(metrics.T_first_failure_system - 1800) < 1


class TestMultiComponentExport:
    """Тесты экспорта многокомпонентной модели"""

    @pytest.fixture
    def sample_results(self, tmp_path):
        """Пример результатов для тестов экспорта"""
        import numpy as np

        # Создаём фиктивные результаты
        t = np.linspace(0, 100, 1000)
        results = {
            'config': {
                'model': {
                    't_span_hours': 100,
                    'n_points': 1000,
                    'control_plane': {'lambda_c': 0.10, 'mu_c': 0.40, 'alpha_cc': 0.05, 'alpha_cp': 0.10},
                    'worker_nodes': {'lambda_w': 0.20, 'mu_w': 0.35, 'alpha_ww': 0.08, 'alpha_wp': 0.12},
                    'pods': {'lambda_p': 0.30, 'mu_p': 0.25, 'alpha_pp': 0.15, 'beta_c': 0.05, 'beta_w': 0.10}
                },
                'probe': {'tau_pcm': 7.70, 'tau_scm': 0.10, 'tau_default': 3.00},
                'thresholds': {'theta_threshold': 0.90, 'theta_critical': 0.50},
                'initial_state': {'C0': 1.0, 'W0': 1.0, 'P0': 1.0},
                'output': {}
            },
            'analytical': {
                'tau_crit_hours': 2.15,
                'tau_crit_seconds': 7740.0,
                'margin_pcm': 99.97,
                'margin_scm': 99.99,
                'margin_default': 99.96
            },
            't': t,
            'C': np.ones_like(t) * 0.95,
            'W': np.ones_like(t) * 0.90,
            'P': np.ones_like(t) * 0.85,
            'metrics': type('obj', (object,), {
                'K_g_C': 99.5, 'P_fail_C': 0.5, 'T_first_failure_C': 5000,
                'K_g_W': 99.0, 'P_fail_W': 1.0, 'T_first_failure_W': 4500,
                'K_g_P': 98.5, 'P_fail_P': 1.5, 'T_first_failure_P': 4000,
                'K_g_avg': 99.0, 'P_fail_avg': 1.0, 'T_first_failure_system': 4000
            })(),
            'metrics_pcm': type('obj', (object,), {
                'K_g_avg': 98.5, 'P_fail_avg': 1.5
            })(),
            'metrics_scm': type('obj', (object,), {
                'K_g_avg': 99.0, 'P_fail_avg': 1.0
            })(),
            'metrics_default': type('obj', (object,), {
                'K_g_avg': 98.7, 'P_fail_avg': 1.3
            })()
        }

        return results, tmp_path

    def test_csv_export_creates_file(self, sample_results):
        """Тест создания CSV файла"""
        results, tmp_path = sample_results
        csv_path = tmp_path / "test_multi.csv"

        save_multi_to_csv(results, str(csv_path))

        assert csv_path.exists()
        assert csv_path.stat().st_size > 0

    def test_csv_export_content(self, sample_results):
        """Тест содержимого CSV файла"""
        results, tmp_path = sample_results
        csv_path = tmp_path / "test_multi.csv"

        save_multi_to_csv(results, str(csv_path))

        # Читаем файл и проверяем наличие ключевых строк
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        assert 'РАЗДЕЛ 1. ИСХОДНЫЕ ДАННЫЕ' in content
        assert 'Control Plane' in content
        assert 'Worker Nodes' in content
        assert 'Pods' in content
        assert 'K_g_C' in content
        assert '99.5' in content  # Одно из значений метрик


class TestIntegration:
    """Интеграционные тесты полного цикла"""

    def test_full_pipeline(self, tmp_path):
        """Тест полного цикла: решение -> метрики -> экспорт"""
        from src.solver_multi import MultiComponentDDESolver
        from src.metrics_multi import calculate_multi_metrics
        from src.export import save_multi_to_csv

        # Параметры
        params = {
            'lambda_c': 0.10, 'mu_c': 0.40, 'alpha_cc': 0.05, 'alpha_cp': 0.10,
            'lambda_w': 0.20, 'mu_w': 0.35, 'alpha_ww': 0.08, 'alpha_wp': 0.12,
            'lambda_p': 0.30, 'mu_p': 0.25, 'alpha_pp': 0.15, 'beta_c': 0.05, 'beta_w': 0.10,
            'C0': 1.0, 'W0': 1.0, 'P0': 1.0
        }

        # Решение
        solver = MultiComponentDDESolver(params, tau=0.001)
        t, y = solver.solve((0, 50), n_points=5000)

        # Метрики
        metrics = calculate_multi_metrics(t, y)

        # Экспорт
        results = {
            'config': {
                'model': params,
                'probe': {'tau_pcm': 7.70, 'tau_scm': 0.10, 'tau_default': 3.00},
                'thresholds': {'theta_threshold': 0.90, 'theta_critical': 0.50},
                'initial_state': {'C0': 1.0, 'W0': 1.0, 'P0': 1.0},
                'output': {}
            },
            'analytical': {'tau_crit_hours': 2.15, 'tau_crit_seconds': 7740.0,
                           'margin_pcm': 99.97, 'margin_scm': 99.99, 'margin_default': 99.96},
            't': t, 'C': y[:, 0], 'W': y[:, 1], 'P': y[:, 2],
            'metrics': metrics,
            'metrics_pcm': metrics,
            'metrics_scm': metrics,
            'metrics_default': metrics
        }

        csv_path = tmp_path / "integration_test.csv"
        save_multi_to_csv(results, str(csv_path))

        # Проверки
        assert csv_path.exists()
        assert metrics.K_g_avg > 0
        assert y.shape == (5000, 3)


# Запуск тестов
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])