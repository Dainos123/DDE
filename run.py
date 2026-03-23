#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа для расчётов отказоустойчивости Kubernetes
"""
import sys
import time
import logging
import argparse
from pathlib import Path

from src.config import FullConfig
from src.solver import DDESolver
from src.metrics import calculate_metrics, critical_delay, stability_margin
from src.visualization import create_plots
from src.export import save_to_csv


def setup_logging(log_file: str, level: int = logging.INFO):
    """Настройка логирования"""
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
    parser = argparse.ArgumentParser(description='Расчёты отказоустойчивости Kubernetes')
    parser.add_argument('--config', type=str, default='configs/default.yaml',
                        help='Путь к YAML конфигурации')
    # FIX: lambda - зарезервированное слово, используем --lambda-f с dest
    parser.add_argument('--lambda-f', type=float, default=None, dest='lambda_f',
                        help='Интенсивность отказов (переопределение)')
    parser.add_argument('--mu', type=float, default=None,
                        help='Интенсивность восстановления (переопределение)')
    parser.add_argument('--no-plots', action='store_true',
                        help='Не создавать графики')
    parser.add_argument('--output-dir', type=str, default='.',
                        help='Папка для вывода файлов')
    return parser.parse_args()


def main():
    start_time = time.time()
    args = parse_args()

    try:
        config = FullConfig.from_yaml(args.config)

        # FIX: используем args.lambda_f вместо args.lambda
        if args.lambda_f is not None:
            config.model.lambda_f = args.lambda_f
        if args.mu is not None:
            config.model.mu_r = args.mu

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        setup_logging(str(output_dir / config.output.log_file))
        logger = logging.getLogger(__name__)

        logger.info("=" * 80)
        logger.info("РАСЧЁТЫ ОТКАЗОУСТОЙЧИВОСТИ KUBERNETES (DDE)")
        logger.info("=" * 80)

        tau_crit = critical_delay(config.model.lambda_f, config.model.mu_r)
        analytical = {
            'tau_crit_hours': tau_crit,
            'tau_crit_seconds': tau_crit * 3600,
            'k_optimal': config.model.mu_r / config.model.lambda_f,
            'theta_optimal': 1.0 - config.model.lambda_f / config.model.mu_r,
            'T_pcm': config.probe.tau_pcm,
            'T_scm': config.probe.tau_scm,
            'improvement': (config.probe.tau_pcm - config.probe.tau_scm) / config.probe.tau_pcm * 100.0,
            'margin_pcm': stability_margin(tau_crit, config.probe.tau_pcm_hours),
            'margin_scm': stability_margin(tau_crit, config.probe.tau_scm_hours),
            'margin_default': stability_margin(tau_crit, config.probe.tau_default_hours)
        }

        logger.info("[1/4] Решение ДУЗ для PCM...")
        solver = DDESolver(config.model)
        t_pcm, x_pcm = solver.solve(config.probe.tau_pcm_hours)

        logger.info("[2/4] Решение ДУЗ для SCM...")
        t_scm, x_scm = solver.solve(config.probe.tau_scm_hours)

        logger.info("[3/4] Решение ДУЗ для Default...")
        t_default, x_default = solver.solve(config.probe.tau_default_hours)

        logger.info("[4/4] Расчёт метрик...")
        metrics_pcm = calculate_metrics(t_pcm, x_pcm, config.thresholds.theta_threshold,
                                        config.thresholds.theta_critical)
        metrics_scm = calculate_metrics(t_scm, x_scm, config.thresholds.theta_threshold,
                                        config.thresholds.theta_critical)
        metrics_default = calculate_metrics(t_default, x_default, config.thresholds.theta_threshold,
                                            config.thresholds.theta_critical)

        results = {
            'config': config,
            'analytical': analytical,
            't_pcm': t_pcm, 'x_pcm': x_pcm,
            't_scm': t_scm, 'x_scm': x_scm,
            't_default': t_default, 'x_default': x_default,
            'metrics_pcm': metrics_pcm,
            'metrics_scm': metrics_scm,
            'metrics_default': metrics_default
        }

        csv_path = output_dir / config.output.csv_file
        save_to_csv(results, str(csv_path))

        if not args.no_plots:
            plot_path = output_dir / config.output.plot_file
            create_plots(results, str(plot_path), config.output.dpi)

        elapsed = time.time() - start_time
        logger.info("=" * 80)
        logger.info("КЛЮЧЕВЫЕ РЕЗУЛЬТАТЫ")
        logger.info("=" * 80)
        logger.info(
            f"Критическое запаздывание τ_crit: {analytical['tau_crit_hours']:.4f} часов ({analytical['tau_crit_seconds']:.2f} сек)")
        logger.info(f"Улучшение времени обнаружения (SCM): {analytical['improvement']:.2f}%")
        logger.info(f"Запас устойчивости (SCM): {analytical['margin_scm']:.4f}%")
        logger.info(f"Коэффициент готовности K_g (SCM): {metrics_scm.K_g:.4f}%")
        logger.info(f"Время выполнения: {elapsed:.2f} секунд")
        logger.info("=" * 80)
        logger.info(f"[OK] Файлы сохранены в: {output_dir.absolute()}")

        return 0

    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())