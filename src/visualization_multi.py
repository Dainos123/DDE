"""Визуализация для многокомпонентной модели"""
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_multi_plots(results: Dict[str, Any], filename: str, dpi: int = 300):
    """Создание 8 графиков для многокомпонентной модели"""
    plt.style.use('seaborn-v0_8-paper')
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('Многокомпонентный анализ отказоустойчивости Kubernetes',
                 fontsize=18, fontweight='bold')

    try:
        _plot_component_dynamics(fig, results)
        _plot_phase_portraits(fig, results)
        _plot_correlation_matrix(fig, results)
        _plot_availability(fig, results)
        _plot_metrics_comparison(fig, results)
        _plot_recovery_time(fig, results)
        _plot_stability_margin_multi(fig, results)
        _plot_component_contribution(fig, results)

        plt.tight_layout()
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close()
        logger.info(f"Многокомпонентные графики сохранены: {filename}")
    except Exception as e:
        logger.error(f"Ошибка создания многокомпонентных графиков: {e}")
        raise


def _plot_component_dynamics(fig, results):
    """График 1: Динамика всех компонентов"""
    ax = fig.add_subplot(3, 3, 1)
    ax.plot(results['t'], results['C'], 'r-', linewidth=2, label='Control Plane', alpha=0.8)
    ax.plot(results['t'], results['W'], 'b-', linewidth=2, label='Worker Nodes', alpha=0.8)
    ax.plot(results['t'], results['P'], 'g-', linewidth=2, label='Pods', alpha=0.8)
    ax.axhline(y=0.9, color='green', linestyle='--', alpha=0.5, label='Порог готовности')
    ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Критический порог')
    ax.set_xlabel('Время (часы)')
    ax.set_ylabel('Доля работоспособных')
    ax.set_title('1. Динамика компонентов Kubernetes')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)


def _plot_phase_portraits(fig, results):
    """График 2: Фазовые портреты"""
    ax = fig.add_subplot(3, 3, 2)
    ax.plot(results['P'], results['C'], '-', alpha=0.5, color='purple')
    ax.set_xlabel('Доля Pod (P)')
    ax.set_ylabel('Доля Control Plane (C)')
    ax.set_title('2. Фазовый портрет C-P')
    ax.grid(True, alpha=0.3)

    ax2 = fig.add_subplot(3, 3, 3)
    ax2.plot(results['P'], results['W'], '-', alpha=0.5, color='orange')
    ax2.set_xlabel('Доля Pod (P)')
    ax2.set_ylabel('Доля Worker Nodes (W)')
    ax2.set_title('3. Фазовый портрет W-P')
    ax2.grid(True, alpha=0.3)


def _plot_correlation_matrix(fig, results):
    """График 4: Корреляция компонентов"""
    ax = fig.add_subplot(3, 3, 4)
    data = np.array([results['C'], results['W'], results['P']])
    corr_matrix = np.corrcoef(data)
    im = ax.imshow(corr_matrix, cmap='RdBu', vmin=-1, vmax=1)
    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    ax.set_xticklabels(['C', 'W', 'P'])
    ax.set_yticklabels(['C', 'W', 'P'])
    ax.set_title('4. Корреляция компонентов')
    plt.colorbar(im, ax=ax, shrink=0.8)

    # Добавить значения на heatmap
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f'{corr_matrix[i, j]:.2f}',
                    ha='center', va='center', fontsize=10)


def _plot_availability(fig, results):
    """График 5: Интегральная доступность"""
    ax = fig.add_subplot(3, 3, 5)
    availability = (results['C'] + results['W'] + results['P']) / 3
    ax.plot(results['t'], availability, 'g-', linewidth=2, label='Средняя доступность')
    ax.axhline(y=0.9, color='green', linestyle='--', label='Порог SLA (0.9)')
    ax.axhline(y=0.99, color='gold', linestyle=':', label='Высокая доступность (0.99)')
    ax.set_xlabel('Время (часы)')
    ax.set_ylabel('Доступность')
    ax.set_title('5. Интегральная доступность кластера')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)


def _plot_metrics_comparison(fig, results):
    """График 6: Сравнение метрик по компонентам"""
    ax = fig.add_subplot(3, 3, 6)
    metrics = ['K_g', 'P_fail']
    labels = ['Готовность (%)', 'Отказы (%)']
    x_pos = np.arange(len(metrics))
    width = 0.25

    m = results['metrics']
    C_vals = [m.K_g_C, m.P_fail_C]
    W_vals = [m.K_g_W, m.P_fail_W]
    P_vals = [m.K_g_P, m.P_fail_P]

    ax.bar(x_pos - width, C_vals, width, label='Control Plane', alpha=0.8, color='red')
    ax.bar(x_pos, W_vals, width, label='Worker Nodes', alpha=0.8, color='blue')
    ax.bar(x_pos + width, P_vals, width, label='Pods', alpha=0.8, color='green')

    ax.set_xlabel('Метрика')
    ax.set_ylabel('Значение (%)')
    ax.set_title('6. Метрики по компонентам')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')


def _plot_recovery_time(fig, results):
    """График 7: Время до отказа по компонентам"""
    ax = fig.add_subplot(3, 3, 7)
    components = ['Control\nPlane', 'Worker\nNodes', 'Pods']
    times = [results['metrics'].T_first_failure_C,
             results['metrics'].T_first_failure_W,
             results['metrics'].T_first_failure_P]
    colors = ['red', 'blue', 'green']

    bars = ax.bar(components, times, color=colors, alpha=0.8)
    ax.set_ylabel('Время до отказа (минуты)')
    ax.set_title('7. Время до первого отказа')
    ax.grid(True, alpha=0.3, axis='y')

    # Добавить значения на столбцы
    for bar, time in zip(bars, times):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50,
                f'{time:.0f}', ha='center', va='bottom', fontsize=9)


def _plot_stability_margin_multi(fig, results):
    """График 8: Запас устойчивости для разных τ"""
    from src.metrics import stability_margin

    ax = fig.add_subplot(3, 3, 8)
    tau_crit = results['analytical']['tau_crit_hours']
    tau_values = np.linspace(0, tau_crit * 1.5, 100)
    margins = [stability_margin(tau_crit, tau) for tau in tau_values]

    ax.plot(tau_values * 3600, margins, 'b-', linewidth=2, label='Запас устойчивости')
    ax.axvline(x=tau_crit * 3600, color='red', linestyle='--',
               label=f'τ_crit = {tau_crit * 3600:.0f}с')
    ax.set_xlabel('Запаздывание τ (секунды)')
    ax.set_ylabel('Запас устойчивости η (%)')
    ax.set_title('8. Запас устойчивости системы')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)


def _plot_component_contribution(fig, results):
    """График 9: Вклад компонентов в общую доступность"""
    ax = fig.add_subplot(3, 3, 9)
    m = results['metrics']

    # Нормализованный вклад в отказы
    total_fail = m.P_fail_C + m.P_fail_W + m.P_fail_P
    if total_fail > 0:
        contributions = [m.P_fail_C / total_fail, m.P_fail_W / total_fail, m.P_fail_P / total_fail]
    else:
        contributions = [0.33, 0.33, 0.34]

    labels = ['Control Plane', 'Worker Nodes', 'Pods']
    colors = ['red', 'blue', 'green']

    wedges, texts, autotexts = ax.pie(contributions, labels=labels, colors=colors,
                                      autopct='%1.1f%%', startangle=90)
    ax.set_title('9. Вклад компонентов в отказы')

    plt.setp(autotexts, size=9, weight='bold')