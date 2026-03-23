Запуск из run.py:
Ограничения:
───────────────────────────────────
1. Не учитывается разделение на Control Plane и Worker Nodes
2. Не моделируются каскадные отказы
3. Параметры λ и μ усреднены по всем компонентам

Запуск из run_multi.py:
Улучшение для каскадных моделей 

- Анализ влияния отказов Control Plane на Pods
- Чувствительность по компонентам
- Оптимальное распределение ресурсов мониторинга

# 1. Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Установка зависимостей
pip install -r requirements.txt

Запуск простой модели

# 3. Базовый запуск
python run.py

# 4. С указанием конфигурации
python run.py --config configs/default.yaml

# 5. Без графиков (только расчёты)
python run.py --no-plots

# 6. С выводом в другую папку
python run.py --output-dir ./results


Запуск расчетов для модели с несколькими задержками

# 3. Базовый запуск
python run_multi.py

# 4. С указанием конфигурации
python run_multi.py --config configs/multi_component.yaml

# 5. Без графиков (только расчёты)
python run_multi.py --no-plots

# 6. С выводом в другую папку
python run_multi.py --output-dir ./results_multi


ЗАПУСК ТЕСТОВ 

# 1. Установите pytest
pip install pytest

# 2. Запустите все тесты
pytest tests/test_multi_solver.py -v

# 3. Запустите с подробным выводом
pytest tests/test_multi_solver.py -v --tb=long

# 4. Запустите конкретный тест
pytest tests/test_multi_solver.py::TestMultiComponentDDESolver::test_solve_returns_correct_shapes -v

# 5. Запустите с покрытием кода (нужен pytest-cov)
pytest tests/test_multi_solver.py -v --cov=src --cov-report=html

Модель Kubernetes с автоскейлингом:

dP/dt = -λ·P(t) + μ·P(t-τ) + α·H(t-τ_h) - β·P(t)·C(t-τ_c)
dC/dt = γ·(P(t) - P_target) - δ·C(t)
dH/dt = ε·(P(t) - P_desired) - ζ·H(t)

P — количество Pod
C — нагрузка на Control Plane
H — Horizontal Pod Autoscaler


Как добавить новое уравнение

Создайте функцию правой части:

def my_equation_rhs(t, y, y_tau):
    # y — текущее состояние
    # y_tau — состояние с запаздыванием
    # Верните dy/dt
    return np.array([...])

Создайте решатель:

solver = MultiComponentDDESolver(
    params={...},  # параметры уравнения
    tau=1.0        # запаздывание
)

Решите:

t, y = solver.solve((0, 100), n_points=10000)

Визуализируйте:

import matplotlib.pyplot as plt
plt.plot(t, y[:, 0], label='Component 1')
plt.plot(t, y[:, 1], label='Component 2')
plt.legend()
plt.show()



Примеры уравнений которые можно расчитать с помощью данной модели 

dx/dt = r · x(t) · [1 - x(t-τ)/K]

Уравнение Хатчинсона (колебания популяции)

dx/dt = r · x(t) · [1 - x(t-τ)/K] - h · x(t)

Уравнение Микаэлиса-Ментен с запаздыванием

dx/dt = V_max · x(t-τ) / (K_m + x(t-τ)) - k · x(t)

Уравнение с триггерной функцией

dx/dt = -a · x(t) + b · tanh(x(t-τ))

Модель "Хищник-Жертва" с запаздыванием

dx/dt = α·x(t) - β·x(t)·y(t-τ)    # Жертвы
dy/dt = δ·x(t-τ)·y(t) - γ·y(t)    # Хищники

Модель иммунного ответа

dV/dt = r·V(t) - k·V(t)·A(t-τ)           # Вирус
dA/dt = α·V(t-τ)·A(t) - δ·A(t)           # Антитела

Эпидемиологическая модель SIR с запаздыванием

dS/dt = -β·S(t)·I(t-τ)/N              # Восприимчивые
dI/dt = β·S(t)·I(t-τ)/N - γ·I(t)      # Заражённые
dR/dt = γ·I(t)                        # Выздоровевшие

Экономическая модель с запаздыванием инвестиций

dK/dt = I(t-τ) - δ·K(t)                # Капитал
dY/dt = α·[C(t) + I(t) - Y(t)]         # Доход
C(t) = c·Y(t)                          # Потребление
I(t) = v·dY/dt                         # Инвестиции

Уравнение с сезонным запаздыванием

dx/dt = -a·x(t) + b·x(t - τ(t))
τ(t) = τ₀ + τ₁·sin(ω·t)

Уравнение Курамото (синхронизация осцилляторов)

dθ_i/dt = ω_i + (K/N) · Σ sin(θ_j(t-τ) - θ_i(t))

Нейронная сеть с запаздыванием

dx_i/dt = -x_i(t) + Σ w_ij · f(x_j(t-τ)) + I_i

