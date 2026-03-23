"""Визуализация результатов"""
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_plots(results: Dict[str, Any], filename: str, dpi: int = 300):
    """Создание 6 графиков анализа"""
    plt.style.use('seaborn-v0_8-paper')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Анализ отказоустойчивости Kubernetes (DDE)', fontsize=16, fontweight='bold')

    try:
        _plot_dynamics(axes[0, 0], results)
        _plot_stability_region(axes[0, 1], results)
        _plot_stability_margin(axes[0, 2], results)
        _plot_sensitivity(axes[1, 0], results)
        _plot_distribution(axes[1, 1], results)
        _plot_metrics_comparison(axes[1, 2], results)

        plt.tight_layout()
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close()
        logger.info(f"Графики сохранены: {filename}")
    except Exception as e:
        logger.error(f"Ошибка создания графиков: {e}")
        raise


def _plot_dynamics(ax, results):
    ax.plot(results['t_pcm'], results['x_pcm'], label='PCM (τ=7.70с)', linewidth=2, alpha=0.8)
    ax.plot(results['t_scm'], results['x_scm'], label='SCM (τ=0.10с)', linewidth=2, alpha=0.8)
    ax.plot(results['t_default'], results['x_default'], label='Default (τ=3.00с)', linewidth=2, alpha=0.8)
    ax.axhline(y=0.9, color='green', linestyle='--', label='Порог готовности (0.9)')
    ax.axhline(y=0.5, color='red', linestyle='--', label='Критический порог (0.5)')
    ax.set_xlabel('Время (часы)')
    ax.set_ylabel('Доля работоспособных Pod')
    ax.set_title('1. Динамика работоспособности кластера')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)


def _plot_stability_region(ax, results):
    from src.metrics import critical_delay
    lambda_vals = np.linspace(0.1, 0.5, 100)
    mu_vals = np.linspace(0.1, 0.5, 100)
    Lambda, Mu = np.meshgrid(lambda_vals, mu_vals)
    Tau_crit = np.zeros_like(Lambda)
    for i in range(len(lambda_vals)):
        for j in range(len(mu_vals)):
            if Mu[j, i] > Lambda[j, i]:
                Tau_crit[j, i] = critical_delay(Lambda[j, i], Mu[j, i])
    contour = ax.contourf(Lambda, Mu, Tau_crit, levels=20, cmap='RdYlGn')
    ax.plot(results['config'].model.lambda_f, results['config'].model.mu_r, 'r*', markersize=15, label='Рабочая точка')
    ax.set_xlabel('λ (интенсивность отказов)')
    ax.set_ylabel('μ (интенсивность восстановления)')
    ax.set_title('2. Область устойчивости (τ_crit, часы)')
    ax.legend()
    plt.colorbar(contour, ax=ax, label='τ_crit (часы)')


def _plot_stability_margin(ax, results):
    from src.metrics import stability_margin
    tau_crit = results['analytical']['tau_crit_hours']
    tau_values = np.linspace(0, tau_crit * 1.5, 100)
    margins = [stability_margin(tau_crit, tau) for tau in tau_values]
    ax.plot(tau_values * 3600, margins, 'b-', linewidth=2, label='Запас устойчивости')
    ax.plot(results['config'].probe.tau_pcm, results['analytical']['margin_pcm'], 'o', markersize=10, label='PCM')
    ax.plot(results['config'].probe.tau_scm, results['analytical']['margin_scm'], 's', markersize=10, label='SCM')
    ax.plot(results['config'].probe.tau_default, results['analytical']['margin_default'], '^', markersize=10,
            label='Default')
    ax.axvline(x=tau_crit * 3600, color='red', linestyle='--', label=f'τ_crit = {tau_crit * 3600:.0f}с')
    ax.set_xlabel('Запаздывание τ (секунды)')
    ax.set_ylabel('Запас устойчивости η (%)')
    ax.set_title('3. Зависимость запаса устойчивости от τ')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)


def _plot_sensitivity(ax, results):
    from src.metrics import critical_delay
    lambda_base = results['config'].model.lambda_f
    mu_base = results['config'].model.mu_r
    lambda_vals = np.linspace(0.1, 0.5, 50)
    tau_crit_lambda = [critical_delay(l, mu_base) for l in lambda_vals]
    mu_vals = np.linspace(0.1, 0.5, 50)
    tau_crit_mu = [critical_delay(lambda_base, m) for m in mu_vals]
    ax.plot(lambda_vals, tau_crit_lambda, 'b-', linewidth=2, label='Влияние λ (μ=0.30)')
    ax.plot(mu_vals, tau_crit_mu, 'r-', linewidth=2, label='Влияние μ (λ=0.25)')
    ax.axvline(x=lambda_base, color='blue', linestyle=':', alpha=0.5)
    ax.axvline(x=mu_base, color='red', linestyle=':', alpha=0.5)
    ax.set_xlabel('Параметр')
    ax.set_ylabel('τ_crit (часы)')
    ax.set_title('4. Анализ чувствительности')
    ax.legend()
    ax.grid(True, alpha=0.3)


def _plot_distribution(ax, results):
    bins = np.linspace(0, 1, 30)
    ax.hist(results['x_pcm'], bins=bins, alpha=0.5, label=f'PCM (среднее={results["metrics_pcm"].x_mean:.2f})')
    ax.hist(results['x_scm'], bins=bins, alpha=0.5, label=f'SCM (среднее={results["metrics_scm"].x_mean:.2f})')
    ax.hist(results['x_default'], bins=bins, alpha=0.5,
            label=f'Default (среднее={results["metrics_default"].x_mean:.2f})')
    ax.set_xlabel('Доля работоспособных Pod')
    ax.set_ylabel('Частота')
    ax.set_title('5. Распределение состояний кластера')
    ax.legend()
    ax.grid(True, alpha=0.3)


def _plot_metrics_comparison(ax, results):
    metrics = ['K_g', 'P_fail']
    labels = ['Готовность (%)', 'Вероятность отказа (%)']
    x_pos = np.arange(len(metrics))
    width = 0.25
    pcm_vals = [results['metrics_pcm'].K_g, results['metrics_pcm'].P_fail]
    scm_vals = [results['metrics_scm'].K_g, results['metrics_scm'].P_fail]
    default_vals = [results['metrics_default'].K_g, results['metrics_default'].P_fail]
    ax.bar(x_pos - width, pcm_vals, width, label='PCM', alpha=0.8)
    ax.bar(x_pos, scm_vals, width, label='SCM', alpha=0.8)
    ax.bar(x_pos + width, default_vals, width, label='Default', alpha=0.8)
    ax.set_xlabel('Метрика')
    ax.set_ylabel('Значение (%)')
    ax.set_title('6. Сравнение метрик отказоустойчивости')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')