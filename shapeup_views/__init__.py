__author__ = 'makoto yamagata'
__version__ = '0.0.6'
__license__ = 'MIT'

__all__ = (
    'View', 'TemplateView', 'FormView',
    'ListView', 'DetailView', 'CreateView', 'UpdateView', 'DeleteView'
)

from django.views.generic import View
from shapeup_views.views import (
    TemplateView, FormView, 
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

