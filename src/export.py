"""Экспорт результатов в CSV для скалярной и многокомпонентной моделей"""
import csv
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# СКАЛЯРНАЯ МОДЕЛЬ
# ============================================================================

def save_to_csv(results: Dict[str, Any], filename: str):
    """Сохранение результатов скалярной модели в CSV"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            _write_header(writer, "ТАБЛИЦА 1. РЕЗУЛЬТАТЫ РАСЧЁТА ПАРАМЕТРОВ ОТКАЗОУСТОЙЧИВОСТИ KUBERNETES")
            _write_section1(writer, results)
            _write_section2(writer, results)
            _write_section3(writer, results)
            _write_section4(writer, results)
            _write_section5(writer, results)
            _write_section6(writer, results)
            _write_section7(writer, results)
            _write_notes(writer)

        logger.info(f"Таблица сохранена: {filename}")
    except Exception as e:
        logger.error(f"Ошибка сохранения CSV: {e}")
        raise


def _write_header(writer, title: str):
    writer.writerow([title])
    writer.writerow([])
    writer.writerow(['№', 'ПАРАМЕТР', 'ОПИСАНИЕ', 'ЗНАЧЕНИЕ', 'ЕД. ИЗМ.'])
    writer.writerow([])


def _write_section1(writer, results):
    cfg = results['config']
    writer.writerow(['', 'РАЗДЕЛ 1. ИСХОДНЫЕ ДАННЫЕ', '', '', ''])
    writer.writerow(['1', 'λ (lambda)', 'Интенсивность отказов', f"{cfg.model.lambda_f:.4f}", '1/час'])
    writer.writerow(['2', 'μ (mu)', 'Интенсивность восстановления', f"{cfg.model.mu_r:.4f}", '1/час'])
    writer.writerow(['3', 'α (alpha)', 'Коэффициент нелинейного взаимодействия', f"{cfg.model.alpha:.4f}", '—'])
    writer.writerow(['4', 'x₀', 'Начальное состояние кластера', f"{cfg.model.x0:.4f}", '—'])
    writer.writerow(['5', 'T', 'Интервал моделирования', f"{cfg.model.t_span_hours:.0f}", 'часы'])
    writer.writerow([])


def _write_section2(writer, results):
    a = results['analytical']
    writer.writerow(['', 'РАЗДЕЛ 2. АНАЛИТИЧЕСКИЕ РАСЧЁТЫ', '', '', ''])
    writer.writerow(
        ['6', 'τ_crit', 'Критическое запаздывание (граница устойчивости)', f"{a['tau_crit_hours']:.4f}", 'часы'])
    writer.writerow(['7', 'τ_crit', 'Критическое запаздывание', f"{a['tau_crit_seconds']:.2f}", 'секунды'])
    writer.writerow(['8', 'k*', 'Оптимальный коэффициент масштабирования', f"{a['k_optimal']:.4f}", '—'])
    writer.writerow(['9', 'θ*', 'Оптимальный порог срабатывания', f"{a['theta_optimal']:.4f}", '—'])
    writer.writerow([])


def _write_section3(writer, results):
    a = results['analytical']
    writer.writerow(['', 'РАЗДЕЛ 3. ВРЕМЯ ОБНАРУЖЕНИЯ ОТКАЗОВ', '', '', ''])
    writer.writerow(['10', 'T_PCM', 'Метод PCM (опрос контейнеров)', f"{a['T_pcm']:.2f}", 'секунды'])
    writer.writerow(['11', 'T_SCM', 'Метод SCM (сигнальный метод)', f"{a['T_scm']:.2f}", 'секунды'])
    writer.writerow(['12', 'T_Default', 'Стандартная конфигурация Kubernetes', '3.00', 'секунды'])
    writer.writerow(['13', 'Δ', 'Улучшение SCM относительно PCM', f"{a['improvement']:.2f}", '%'])
    writer.writerow([])


def _write_section4(writer, results):
    a = results['analytical']
    writer.writerow(['', 'РАЗДЕЛ 4. ЗАПАС УСТОЙЧИВОСТИ', '', '', ''])
    writer.writerow(['14', 'η_PCM', 'Запас устойчивости (PCM)', f"{a['margin_pcm']:.4f}", '%'])
    writer.writerow(['15', 'η_SCM', 'Запас устойчивости (SCM)', f"{a['margin_scm']:.4f}", '%'])
    writer.writerow(['16', 'η_Default', 'Запас устойчивости (Default)', f"{a['margin_default']:.4f}", '%'])
    writer.writerow([])


def _write_section5(writer, results):
    m = results['metrics_pcm']
    writer.writerow(['', 'РАЗДЕЛ 5. МЕТРИКИ РАБОТОСПОСОБНОСТИ (PCM)', '', '', ''])
    writer.writerow(['17', 'K_g', 'Коэффициент готовности', f"{m.K_g:.4f}", '%'])
    writer.writerow(['18', 'P_fail', 'Вероятность отказа', f"{m.P_fail:.2f}", '%'])
    writer.writerow(['19', 'T_first', 'Время до первого отказа', f"{m.T_first_failure:.2f}", 'минуты'])
    writer.writerow(['20', 'x_mean', 'Средняя доля работоспособных Pod', f"{m.x_mean:.4f}", '—'])
    writer.writerow([])


def _write_section6(writer, results):
    m = results['metrics_scm']
    writer.writerow(['', 'РАЗДЕЛ 6. МЕТРИКИ РАБОТОСПОСОБНОСТИ (SCM)', '', '', ''])
    writer.writerow(['21', 'K_g', 'Коэффициент готовности', f"{m.K_g:.4f}", '%'])
    writer.writerow(['22', 'P_fail', 'Вероятность отказа', f"{m.P_fail:.2f}", '%'])
    writer.writerow(['23', 'T_first', 'Время до первого отказа', f"{m.T_first_failure:.2f}", 'минуты'])
    writer.writerow(['24', 'x_mean', 'Средняя доля работоспособных Pod', f"{m.x_mean:.4f}", '—'])
    writer.writerow(['25', 'x_min', 'Минимальная доля работоспособных Pod', f"{m.x_min:.4f}", '—'])
    writer.writerow(['26', 'x_max', 'Максимальная доля работоспособных Pod', f"{m.x_max:.4f}", '—'])
    writer.writerow([])


def _write_section7(writer, results):
    m = results['metrics_default']
    writer.writerow(['', 'РАЗДЕЛ 7. МЕТРИКИ РАБОТОСПОСОБНОСТИ (DEFAULT)', '', '', ''])
    writer.writerow(['27', 'K_g', 'Коэффициент готовности', f"{m.K_g:.4f}", '%'])
    writer.writerow(['28', 'P_fail', 'Вероятность отказа', f"{m.P_fail:.2f}", '%'])
    writer.writerow(['29', 'T_first', 'Время до первого отказа', f"{m.T_first_failure:.2f}", 'минуты'])
    writer.writerow(['30', 'x_mean', 'Средняя доля работоспособных Pod', f"{m.x_mean:.4f}", '—'])
    writer.writerow([])


def _write_notes(writer):
    writer.writerow(['', 'ПРИМЕЧАНИЕ', '', '', ''])
    writer.writerow(['', '* Базовая конфигурация без алгоритма проактивного масштабирования', '', '', ''])
    writer.writerow(['', '** При внедрении проактивного масштабирования ожидается K_g до 95-98%', '', '', ''])


# ============================================================================
# МНОГОКОМПОНЕНТНАЯ МОДЕЛЬ
# ============================================================================

def save_multi_to_csv(results: Dict[str, Any], filename: str):
    """
    Сохранение результатов многокомпонентной модели в CSV

    Args:
        results: Словарь с результатами расчётов
        filename: Имя выходного файла
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')

            # Заголовок
            _write_multi_header(writer)

            # Разделы
            _write_multi_section1(writer, results)  # Исходные данные
            _write_multi_section2(writer, results)  # Аналитические расчёты
            _write_multi_section3(writer, results)  # Время обнаружения
            _write_multi_section4(writer, results)  # Запас устойчивости
            _write_multi_section5(writer, results)  # Метрики Control Plane
            _write_multi_section6(writer, results)  # Метрики Worker Nodes
            _write_multi_section7(writer, results)  # Метрики Pods
            _write_multi_section8(writer, results)  # Интегральные метрики системы
            _write_multi_section9(writer, results)  # Сравнение PCM/SCM/Default
            _write_multi_notes(writer)

        logger.info(f"Многокомпонентная таблица сохранена: {filename}")
    except Exception as e:
        logger.error(f"Ошибка сохранения многокомпонентной CSV: {e}")
        raise


def _write_multi_header(writer):
    """Заголовок таблицы"""
    writer.writerow(['ТАБЛИЦА 2. РЕЗУЛЬТАТЫ МНОГОКОМПОНЕНТНОГО АНАЛИЗА ОТКАЗОУСТОЙЧИВОСТИ KUBERNETES'])
    writer.writerow([])
    writer.writerow(['№', 'ПАРАМЕТР', 'ОПИСАНИЕ', 'ЗНАЧЕНИЕ', 'ЕД. ИЗМ.'])
    writer.writerow([])


def _write_multi_section1(writer, results):
    """Раздел 1: Исходные данные"""
    cfg = results['config']
    m = cfg['model']
    init = cfg['initial_state']

    writer.writerow(['', 'РАЗДЕЛ 1. ИСХОДНЫЕ ДАННЫЕ', '', '', ''])
    writer.writerow(['1', 'T', 'Интервал моделирования', f"{m['t_span_hours']:.0f}", 'часы'])
    writer.writerow(['2', 'N_points', 'Количество точек дискретизации', f"{m['n_points']:.0f}", '—'])
    writer.writerow([])

    writer.writerow(['', 'Control Plane:', '', '', ''])
    writer.writerow(
        ['3', 'λ_c', 'Интенсивность отказов Control Plane', f"{m['control_plane']['lambda_c']:.4f}", '1/час'])
    writer.writerow(
        ['4', 'μ_c', 'Интенсивность восстановления Control Plane', f"{m['control_plane']['mu_c']:.4f}", '1/час'])
    writer.writerow(
        ['5', 'α_cc', 'Внутреннее взаимодействие Control Plane', f"{m['control_plane']['alpha_cc']:.4f}", '—'])
    writer.writerow(['6', 'α_cp', 'Влияние Pods на Control Plane', f"{m['control_plane']['alpha_cp']:.4f}", '—'])
    writer.writerow(['7', 'C₀', 'Начальное состояние Control Plane', f"{init['C0']:.4f}", '—'])
    writer.writerow([])

    writer.writerow(['', 'Worker Nodes:', '', '', ''])
    writer.writerow(['8', 'λ_w', 'Интенсивность отказов Worker Nodes', f"{m['worker_nodes']['lambda_w']:.4f}", '1/час'])
    writer.writerow(
        ['9', 'μ_w', 'Интенсивность восстановления Worker Nodes', f"{m['worker_nodes']['mu_w']:.4f}", '1/час'])
    writer.writerow(
        ['10', 'α_ww', 'Внутреннее взаимодействие Worker Nodes', f"{m['worker_nodes']['alpha_ww']:.4f}", '—'])
    writer.writerow(['11', 'α_wp', 'Влияние Pods на Worker Nodes', f"{m['worker_nodes']['alpha_wp']:.4f}", '—'])
    writer.writerow(['12', 'W₀', 'Начальное состояние Worker Nodes', f"{init['W0']:.4f}", '—'])
    writer.writerow([])

    writer.writerow(['', 'Pods:', '', '', ''])
    writer.writerow(['13', 'λ_p', 'Интенсивность отказов Pods', f"{m['pods']['lambda_p']:.4f}", '1/час'])
    writer.writerow(['14', 'μ_p', 'Интенсивность восстановления Pods', f"{m['pods']['mu_p']:.4f}", '1/час'])
    writer.writerow(['15', 'α_pp', 'Внутреннее взаимодействие Pods', f"{m['pods']['alpha_pp']:.4f}", '—'])
    writer.writerow(['16', 'β_c', 'Влияние Control Plane на Pods', f"{m['pods']['beta_c']:.4f}", '—'])
    writer.writerow(['17', 'β_w', 'Влияние Worker Nodes на Pods', f"{m['pods']['beta_w']:.4f}", '—'])
    writer.writerow(['18', 'P₀', 'Начальное состояние Pods', f"{init['P0']:.4f}", '—'])
    writer.writerow([])


def _write_multi_section2(writer, results):
    """Раздел 2: Аналитические расчёты"""
    a = results['analytical']

    writer.writerow(['', 'РАЗДЕЛ 2. АНАЛИТИЧЕСКИЕ РАСЧЁТЫ', '', '', ''])
    writer.writerow(['19', 'τ_crit', 'Критическое запаздывание (Control Plane)', f"{a['tau_crit_hours']:.4f}", 'часы'])
    writer.writerow(['20', 'τ_crit', 'Критическое запаздывание', f"{a['tau_crit_seconds']:.2f}", 'секунды'])
    writer.writerow([])


def _write_multi_section3(writer, results):
    """Раздел 3: Время обнаружения отказов"""
    cfg = results['config']
    probe = cfg['probe']

    writer.writerow(['', 'РАЗДЕЛ 3. ВРЕМЯ ОБНАРУЖЕНИЯ ОТКАЗОВ', '', '', ''])
    writer.writerow(['21', 'T_PCM', 'Метод PCM (опрос контейнеров)', f"{probe['tau_pcm']:.2f}", 'секунды'])
    writer.writerow(['22', 'T_SCM', 'Метод SCM (сигнальный метод)', f"{probe['tau_scm']:.2f}", 'секунды'])
    writer.writerow(
        ['23', 'T_Default', 'Стандартная конфигурация Kubernetes', f"{probe['tau_default']:.2f}", 'секунды'])
    writer.writerow(['24', 'Δ', 'Улучшение SCM относительно PCM',
                     f"{(probe['tau_pcm'] - probe['tau_scm']) / probe['tau_pcm'] * 100:.2f}", '%'])
    writer.writerow([])


def _write_multi_section4(writer, results):
    """Раздел 4: Запас устойчивости"""
    a = results['analytical']

    writer.writerow(['', 'РАЗДЕЛ 4. ЗАПАС УСТОЙЧИВОСТИ', '', '', ''])
    writer.writerow(['25', 'η_PCM', 'Запас устойчивости (PCM)', f"{a['margin_pcm']:.4f}", '%'])
    writer.writerow(['26', 'η_SCM', 'Запас устойчивости (SCM)', f"{a['margin_scm']:.4f}", '%'])
    writer.writerow(['27', 'η_Default', 'Запас устойчивости (Default)', f"{a['margin_default']:.4f}", '%'])
    writer.writerow([])


def _write_multi_section5(writer, results):
    """Раздел 5: Метрики Control Plane (SCM)"""
    m = results['metrics_scm']

    writer.writerow(['', 'РАЗДЕЛ 5. МЕТРИКИ CONTROL PLANE (SCM)', '', '', ''])
    writer.writerow(['28', 'K_g_C', 'Коэффициент готовности Control Plane', f"{m.K_g_C:.4f}", '%'])
    writer.writerow(['29', 'P_fail_C', 'Вероятность отказа Control Plane', f"{m.P_fail_C:.2f}", '%'])
    writer.writerow(
        ['30', 'T_first_C', 'Время до первого отказа Control Plane', f"{m.T_first_failure_C:.2f}", 'минуты'])
    writer.writerow([])


def _write_multi_section6(writer, results):
    """Раздел 6: Метрики Worker Nodes (SCM)"""
    m = results['metrics_scm']

    writer.writerow(['', 'РАЗДЕЛ 6. МЕТРИКИ WORKER NODES (SCM)', '', '', ''])
    writer.writerow(['31', 'K_g_W', 'Коэффициент готовности Worker Nodes', f"{m.K_g_W:.4f}", '%'])
    writer.writerow(['32', 'P_fail_W', 'Вероятность отказа Worker Nodes', f"{m.P_fail_W:.2f}", '%'])
    writer.writerow(['33', 'T_first_W', 'Время до первого отказа Worker Nodes', f"{m.T_first_failure_W:.2f}", 'минуты'])
    writer.writerow([])


def _write_multi_section7(writer, results):
    """Раздел 7: Метрики Pods (SCM)"""
    m = results['metrics_scm']

    writer.writerow(['', 'РАЗДЕЛ 7. МЕТРИКИ PODS (SCM)', '', '', ''])
    writer.writerow(['34', 'K_g_P', 'Коэффициент готовности Pods', f"{m.K_g_P:.4f}", '%'])
    writer.writerow(['35', 'P_fail_P', 'Вероятность отказа Pods', f"{m.P_fail_P:.2f}", '%'])
    writer.writerow(['36', 'T_first_P', 'Время до первого отказа Pods', f"{m.T_first_failure_P:.2f}", 'минуты'])
    writer.writerow([])


def _write_multi_section8(writer, results):
    """Раздел 8: Интегральные метрики системы"""
    m = results['metrics_scm']

    writer.writerow(['', 'РАЗДЕЛ 8. ИНТЕГРАЛЬНЫЕ МЕТРИКИ СИСТЕМЫ', '', '', ''])
    writer.writerow(['37', 'K_g_avg', 'Средняя доступность системы', f"{m.K_g_avg:.4f}", '%'])
    writer.writerow(['38', 'P_fail_avg', 'Средняя вероятность отказа системы', f"{m.P_fail_avg:.2f}", '%'])
    writer.writerow(
        ['39', 'T_first_sys', 'Время до первого отказа системы', f"{m.T_first_failure_system:.2f}", 'минуты'])
    writer.writerow([])


def _write_multi_section9(writer, results):
    """Раздел 9: Сравнение методов обнаружения"""
    m_pcm = results['metrics_pcm']
    m_scm = results['metrics_scm']
    m_def = results['metrics_default']

    writer.writerow(['', 'РАЗДЕЛ 9. СРАВНЕНИЕ МЕТОДОВ ОБНАРУЖЕНИЯ', '', '', ''])
    writer.writerow(['', 'Коэффициент готовности (K_g):', '', '', ''])
    writer.writerow(['40', 'K_g_PCM', 'Метод PCM', f"{m_pcm.K_g_avg:.4f}", '%'])
    writer.writerow(['41', 'K_g_SCM', 'Метод SCM', f"{m_scm.K_g_avg:.4f}", '%'])
    writer.writerow(['42', 'K_g_Default', 'Метод Default', f"{m_def.K_g_avg:.4f}", '%'])
    writer.writerow(['43', 'ΔK_g', 'Улучшение SCM относительно PCM', f"{m_scm.K_g_avg - m_pcm.K_g_avg:.4f}", '%'])
    writer.writerow([])

    writer.writerow(['', 'Вероятность отказа (P_fail):', '', '', ''])
    writer.writerow(['44', 'P_fail_PCM', 'Метод PCM', f"{m_pcm.P_fail_avg:.2f}", '%'])
    writer.writerow(['45', 'P_fail_SCM', 'Метод SCM', f"{m_scm.P_fail_avg:.2f}", '%'])
    writer.writerow(['46', 'P_fail_Default', 'Метод Default', f"{m_def.P_fail_avg:.2f}", '%'])
    writer.writerow(
        ['47', 'ΔP_fail', 'Улучшение SCM относительно PCM', f"{m_pcm.P_fail_avg - m_scm.P_fail_avg:.2f}", '%'])
    writer.writerow([])


def _write_multi_notes(writer):
    """Примечания"""
    writer.writerow(['', 'ПРИМЕЧАНИЕ', '', '', ''])
    writer.writerow(['', '* Control Plane: API Server, etcd, Controller Manager, Scheduler', '', '', ''])
    writer.writerow(['', '** Worker Nodes: Узлы для размещения Pod с контейнерами', '', '', ''])
    writer.writerow(['', '*** Pods: Минимальная единица развёртывания в Kubernetes', '', '', ''])
    writer.writerow(['', '**** При внедрении проактивного обнаружения (SCM) ожидается K_g до 99.5%+', '', '', ''])