"""Transduction layer for converting SimPy observables to MES format.

This module provides the transduction layer that extracts MES-visible
information from the comprehensive SimPy event stream.
"""

from .mes_transducer import MESTransducer

__all__ = ["MESTransducer"]
