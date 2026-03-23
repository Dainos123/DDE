#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа для многокомпонентной модели Kubernetes
Моделирует отказоустойчивость трёх компонентов:
- Control Plane (API Server, etcd, Controller Manager, Scheduler)
- Worker Nodes
- Pods
"""
import sys
import time
import logging
import argparse
from pathlib import Path
import numpy as np

from src.config import FullConfig
from src.solver_multi import MultiComponentDDESolver
from src.metrics_multi import calculate_multi_metrics
from src.metrics import critical_delay, stability_margin
from src.visualization_multi import create_multi_plots
from src.export import save_multi_to_csv


def setup_logging(log_file: str, level: int = logging.INFO):
    """
    Настройка логирования

    Args:
        log_file: Путь к файлу лога
        level: Уровень логирования
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def parse_args():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='Многокомпонентные расчёты отказоустойчивости Kubernetes'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='configs/multi_component.yaml',
        help='Путь к YAML конфигурации (по умолчанию: configs/multi_component.yaml)'
    )
    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Не создавать графики'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Папка для вывода файлов (по умолчанию: текущая директория)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Включить подробное логирование (DEBUG уровень)'
    )
    return parser.parse_args()


def load_multi_config(config_path: str) -> dict:
    """
    Загрузка конфигурации для многокомпонентной модели

    Args:
        config_path: Путь к YAML файлу конфигурации

    Returns:
        Словарь с конфигурацией

    Raises:
        FileNotFoundError: Если файл конфигурации не найден
        yaml.YAMLError: Если ошибка парсинга YAML
    """
    import yaml

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Валидация обязательных секций
        required_sections = ['model', 'probe', 'thresholds', 'initial_state', 'output']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Отсутствует обязательная секция '{section}' в конфигурации")

        return config

    except FileNotFoundError:
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Ошибка парсинга YAML конфигурации: {e}")


def main():
    """Основная функция расчётов многокомпонентной модели"""
    start_time = time.time()
    args = parse_args()

    # Настройка уровня логирования
    log_level = logging.DEBUG if args.verbose else logging.INFO

    try:
        # Загрузка конфигурации
        config = load_multi_config(args.config)

        # Создание директории для вывода
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Настройка логирования
        log_file_path = output_dir / config['output']['log_file']
        setup_logging(str(log_file_path), level=log_level)

        logger = logging.getLogger(__name__)

        logger.info("=" * 80)
        logger.info("МНОГОКОМПОНЕНТНЫЕ РАСЧЁТЫ ОТКАЗОУСТОЙЧИВОСТИ KUBERNETES")
        logger.info("=" * 80)
        logger.info(f"Конфигурация загружена из: {args.config}")
        logger.info(f"Директория вывода: {output_dir.absolute()}")
        logger.info("")

        # Извлечение параметров из конфигурации
        p = config['model']
        probe = config['probe']
        thresholds = config['thresholds']
        initial = config['initial_state']

        # Аналитические расчёты (для Control Plane как основного компонента)
        logger.info("Выполнение аналитических расчётов...")
        tau_crit = critical_delay(
            p['control_plane']['lambda_c'],
            p['control_plane']['mu_c']
        )

        analytical = {
            'tau_crit_hours': tau_crit,
            'tau_crit_seconds': tau_crit * 3600,
            'margin_pcm': stability_margin(tau_crit, probe['tau_pcm'] / 3600),
            'margin_scm': stability_margin(tau_crit, probe['tau_scm'] / 3600),
            'margin_default': stability_margin(tau_crit, probe['tau_default'] / 3600)
        }

        logger.info(f"Критическое запаздывание τ_crit: {tau_crit:.4f} часов ({tau_crit * 3600:.2f} сек)")
        logger.info("")

        # Подготовка параметров для решателя
        solver_params = {
            **p['control_plane'],
            **p['worker_nodes'],
            **p['pods'],
            'C0': initial['C0'],
            'W0': initial['W0'],
            'P0': initial['P0']
        }

        t_span = (0, p['t_span_hours'])
        n_points = p['n_points']

        # Решение для PCM
        logger.info("[1/3] Решение ДУЗ для PCM (τ=7.70с)...")
        solver_pcm = MultiComponentDDESolver(solver_params, probe['tau_pcm'] / 3600)
        t_pcm, y_pcm = solver_pcm.solve(t_span, n_points=n_points)
        logger.debug(f"  PCM: t.shape={t_pcm.shape}, y.shape={y_pcm.shape}")

        # Решение для SCM
        logger.info("[2/3] Решение ДУЗ для SCM (τ=0.10с)...")
        solver_scm = MultiComponentDDESolver(solver_params, probe['tau_scm'] / 3600)
        t_scm, y_scm = solver_scm.solve(t_span, n_points=n_points)
        logger.debug(f"  SCM: t.shape={t_scm.shape}, y.shape={y_scm.shape}")

        # Решение для Default
        logger.info("[3/3] Решение ДУЗ для Default (τ=3.00с)...")
        solver_default = MultiComponentDDESolver(solver_params, probe['tau_default'] / 3600)
        t_default, y_default = solver_default.solve(t_span, n_points=n_points)
        logger.debug(f"  Default: t.shape={t_default.shape}, y.shape={y_default.shape}")

        # Расчёт метрик
        logger.info("[4/4] Расчёт метрик...")
        metrics_pcm = calculate_multi_metrics(
            t_pcm, y_pcm,
            thresholds['theta_threshold'],
            thresholds['theta_critical']
        )
        metrics_scm = calculate_multi_metrics(
            t_scm, y_scm,
            thresholds['theta_threshold'],
            thresholds['theta_critical']
        )
        metrics_default = calculate_multi_metrics(
            t_default, y_default,
            thresholds['theta_threshold'],
            thresholds['theta_critical']
        )
        logger.debug(f"  Метрики SCM: K_g_avg={metrics_scm.K_g_avg:.4f}%")

        # Подготовка результатов для визуализации (SCM как основной метод)
        results = {
            'config': config,
            'analytical': analytical,
            't': t_scm,
            'C': y_scm[:, 0],  # Control Plane
            'W': y_scm[:, 1],  # Worker Nodes
            'P': y_scm[:, 2],  # Pods
            'metrics': metrics_scm,
            'metrics_pcm': metrics_pcm,
            'metrics_scm': metrics_scm,
            'metrics_default': metrics_default
        }

        # Экспорт в CSV
        logger.info("Экспорт результатов в CSV...")
        csv_path = output_dir / config['output']['csv_file']
        save_multi_to_csv(results, str(csv_path))

        # Создание графиков
        if not args.no_plots:
            logger.info("Создание графиков...")
            plot_path = output_dir / config['output']['plot_file']
            create_multi_plots(results, str(plot_path), config['output']['dpi'])
        else:
            logger.info("Создание графиков пропущено (--no-plots)")

        # Расчёт времени выполнения
        elapsed = time.time() - start_time

        # Вывод ключевых результатов
        logger.info("")
        logger.info("=" * 80)
        logger.info("КЛЮЧЕВЫЕ РЕЗУЛЬТАТЫ (SCM)")
        logger.info("=" * 80)
        logger.info(
            f"Критическое запаздывание τ_crit: {analytical['tau_crit_hours']:.4f} часов ({analytical['tau_crit_seconds']:.2f} сек)")
        logger.info(f"Запас устойчивости (SCM): {analytical['margin_scm']:.4f}%")
        logger.info("")
        logger.info("Control Plane:")
        logger.info(f"  K_g = {metrics_scm.K_g_C:.4f}%, P_fail = {metrics_scm.P_fail_C:.2f}%")
        logger.info(f"  T_first_failure = {metrics_scm.T_first_failure_C:.2f} минут")
        logger.info("Worker Nodes:")
        logger.info(f"  K_g = {metrics_scm.K_g_W:.4f}%, P_fail = {metrics_scm.P_fail_W:.2f}%")
        logger.info(f"  T_first_failure = {metrics_scm.T_first_failure_W:.2f} минут")
        logger.info("Pods:")
        logger.info(f"  K_g = {metrics_scm.K_g_P:.4f}%, P_fail = {metrics_scm.P_fail_P:.2f}%")
        logger.info(f"  T_first_failure = {metrics_scm.T_first_failure_P:.2f} минут")
        logger.info("")
        logger.info("Интегральные метрики системы:")
        logger.info(f"  Средняя доступность: {metrics_scm.K_g_avg:.4f}%")
        logger.info(f"  Средняя вероятность отказа: {metrics_scm.P_fail_avg:.2f}%")
        logger.info(f"  Время до первого отказа системы: {metrics_scm.T_first_failure_system:.2f} минут")
        logger.info("")
        logger.info(f"Время выполнения: {elapsed:.2f} секунд")
        logger.info("=" * 80)
        logger.info(f"[OK] Файлы сохранены в: {output_dir.absolute()}")
        logger.info(f"  - {csv_path.name}")
        if not args.no_plots:
            logger.info(f"  - {config['output']['plot_file']}")
        logger.info(f"  - {config['output']['log_file']}")
        logger.info("=" * 80)

        return 0

    except FileNotFoundError as e:
        logging.error(f"Ошибка: {e}")
        return 1
    except ValueError as e:
        logging.error(f"Ошибка валидации: {e}", exc_info=args.verbose)
        return 2
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)
        return 3


if __name__ == '__main__':
    sys.exit(main())