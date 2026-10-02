"""Temperature scaling utilities for probability calibration.

Calibration is optional and artifact-driven. The API must never label a model
as calibrated unless a fitted artifact exists and is successfully loaded.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

import numpy as np


def _clip(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=np.float64), 1e-7, 1.0 - 1e-7)


def _logit(p: np.ndarray) -> np.ndarray:
    p = _clip(p)
    return np.log(p / (1.0 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))


def binary_nll(y_true: np.ndarray, p: np.ndarray) -> float:
    p = _clip(p)
    y = np.asarray(y_true, dtype=np.float64)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


class TemperatureScaler:
    """Binary temperature scaler fitted by deterministic grid search."""

    def __init__(self, temperature: float = 1.0, fitted: bool = False, source: str = "none"):
        self.temperature = float(max(0.05, temperature))
        self.fitted = bool(fitted)
        self.source = str(source)

    def fit(self, y_true: Iterable[int], probabilities: Iterable[float]) -> dict:
        y = np.asarray(list(y_true), dtype=np.int32)
        p = _clip(np.asarray(list(probabilities), dtype=np.float64))
        if len(y) != len(p) or len(y) < 20:
            raise ValueError("At least 20 matching validation labels/probabilities are required.")
        if np.any((y != 0) & (y != 1)):
            raise ValueError("Binary calibration labels must be 0 or 1.")

        logits = _logit(p)
        # Dense deterministic search is robust and avoids scipy dependency.
        grid = np.geomspace(0.05, 10.0, 400)
        losses = []
        for t in grid:
            calibrated = _sigmoid(logits / t)
            losses.append(binary_nll(y, calibrated))
        best_idx = int(np.argmin(losses))
        self.temperature = float(grid[best_idx])
        self.fitted = True
        self.source = "validation_grid_search"
        return {
            "temperature": self.temperature,
            "validation_nll": float(losses[best_idx]),
            "uncalibrated_nll": binary_nll(y, p),
            "samples": int(len(y)),
            "source": self.source,
        }

    def transform(self, probability: float) -> float:
        if not self.fitted:
            return float(np.clip(probability, 0.0, 1.0))
        return float(_sigmoid(np.asarray(_logit(np.asarray([probability])) / self.temperature))[0])

    def save(self, path: str | Path, metadata: Optional[dict] = None) -> None:
        payload = {
            "method": "temperature_scaling",
            "temperature": self.temperature,
            "fitted": self.fitted,
            "source": self.source,
            "metadata": metadata or {},
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "TemperatureScaler":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("method") != "temperature_scaling":
            raise ValueError("Unsupported calibration artifact method.")
        return cls(
            temperature=float(payload["temperature"]),
            fitted=bool(payload.get("fitted", True)),
            source=str(payload.get("source", "artifact")),
        )
