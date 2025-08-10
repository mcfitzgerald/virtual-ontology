"""
Virtual Twin Database Setup Module
Provides comprehensive database initialization and management functionality
"""

from .twin_tables import TwinTablesManager
from .mes_historical import MESHistoricalDataGenerator

__version__ = "1.0.0"
__all__ = ["TwinTablesManager", "MESHistoricalDataGenerator"]