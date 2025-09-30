"""
UI modules for KB Admin
Модули пользовательского интерфейса
"""

from .ui_components import (
    render_user_view, 
    render_standard_reports, 
    render_custom_query,
    render_smart_assistant, 
    render_help, 
    render_staff_view
)
from .main_interface import KBAdminInterface
from .testing_interface import TestingInterface

__all__ = [
    'render_user_view', 'render_standard_reports', 'render_custom_query',
    'render_smart_assistant', 'render_help', 'render_staff_view',
    'KBAdminInterface', 'TestingInterface'
]
