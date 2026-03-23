import pytest
import numpy as np
from src.metrics import calculate_metrics, critical_delay, stability_margin

def test_critical_delay_valid():
    assert critical_delay(0.25, 0.30) > 0

def test_critical_delay_invalid():
    assert critical_delay(0.30, 0.25) == float('inf')

def test_metrics_range():
    t = np.linspace(0, 10, 100)
    x = np.ones(100) * 0.95
    m = calculate_metrics(t, x)
    assert 0 <= m.K_g <= 100
    assert 0 <= m.P_fail <= 100

def test_stability_margin():
    assert stability_margin(10.0, 5.0) == 50.0
    assert stability_margin(10.0, 10.0) == 0.0