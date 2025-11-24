#!/usr/bin/env python3
"""
Parser Strategies - Different approaches to CV parsing
"""

from .pattern_strategy import PatternStrategy
from .openai_strategy import OpenAIStrategy
from .hybrid_strategy import HybridStrategy

__all__ = ['PatternStrategy', 'OpenAIStrategy', 'HybridStrategy']

