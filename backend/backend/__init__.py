"""
Backend package initializer.

This module exposes the Celery application instance so that other modules can
import it as `from backend import celery_app`.  Celery will automatically
discover tasks defined in any installed Django apps when it is initialised.
"""
from __future__ import annotations

from .celery import app as celery_app  # noqa: F401

__all__ = ("celery_app",)