"""Конфигурация модели и валидация параметров"""
from dataclasses import dataclass, field
from typing import Optional
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Конфигурация математической модели"""
    lambda_f: float = 0.25
    mu_r: float = 0.30
    alpha: float = 0.15
    x0: float = 1.0
    t_span_hours: float = 100
    n_points: int = 10000

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if self.lambda_f <= 0:
            raise ValueError("λ (lambda_f) должна быть > 0")
        if self.mu_r <= 0:
            raise ValueError("μ (mu_r) должна быть > 0")
        if self.alpha < 0:
            raise ValueError("α (alpha) должна быть >= 0")
        if self.mu_r <= self.lambda_f:
            logger.warning("μ ≤ λ - система может быть неустойчива!")


@dataclass
class ProbeConfig:
    """Конфигурация методов обнаружения"""
    n_probe: int = 3
    i_probe: float = 3.0
    l_probe: float = 0.2
    l_signal: float = 0.1
    tau_default: float = 3.0

    @property
    def tau_pcm(self) -> float:
        return (self.n_probe - 0.5) * self.i_probe + self.l_probe

    @property
    def tau_scm(self) -> float:
        return self.l_signal

    @property
    def tau_pcm_hours(self) -> float:
        return self.tau_pcm / 3600.0

    @property
    def tau_scm_hours(self) -> float:
        return self.tau_scm / 3600.0

    @property
    def tau_default_hours(self) -> float:
        return self.tau_default / 3600.0


@dataclass
class ThresholdConfig:
    """Пороговые значения"""
    theta_threshold: float = 0.90
    theta_critical: float = 0.50


@dataclass
class OutputConfig:
    """Настройки вывода"""
    csv_file: str = "vak_article_table_ru.csv"
    plot_file: str = "kubernetes_dde_calculations.png"
    log_file: str = "calculations.log"
    dpi: int = 300


@dataclass
class FullConfig:
    """Полная конфигурация проекта"""
    model: ModelConfig = field(default_factory=ModelConfig)
    probe: ProbeConfig = field(default_factory=ProbeConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_yaml(cls, path: str) -> 'FullConfig':
        """Загрузка конфигурации из YAML файла"""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return cls(
            model=ModelConfig(**data.get('model', {})),
            probe=ProbeConfig(**data.get('probe', {})),
            thresholds=ThresholdConfig(**data.get('thresholds', {})),
            output=OutputConfig(**data.get('output', {}))
        )

    @classmethod
    def default(cls) -> 'FullConfig':
        """Конфигурация по умолчанию"""
        return cls()