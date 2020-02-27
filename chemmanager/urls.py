from django.urls import path
from .views import (
    ChemicalListView,
    ChemicalUpdateView,
    ChemicalCreateView,
    StockCreateView,
    StockDetailView,
    ChemicalDeleteView,
)
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('', login_required(ChemicalListView.as_view()), name='chemmanager-home'),
    path('chemical/<int:pk>/update', ChemicalUpdateView.as_view(), name='chemical-detail'),
    path('chemical/new/', login_required(ChemicalCreateView.as_view()), name='chemical-create'),
    path('stock/<int:pk>/new/', login_required(StockCreateView.as_view()), name='stock-create'),
    path('stock/<int:pk>/', login_required(StockDetailView.as_view()), name='stock-detail'),
    path('chemical/<int:pk>/delete', ChemicalDeleteView.as_view(), name='chemical-delete')
]