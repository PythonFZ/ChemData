from django.urls import path
from .views import (
    ChemicalListView,
    ChemicalUpdateView,
    ChemicalCreateView,
    StockCreateView,
    StockUpdateView,
    ChemicalDeleteView,
    ExtractionCreateView,
    StockDeleteView,
    StorageListView,
    StorageCreateView,
    StorageDeleteView,
    ChemicalDetailView,
    StorageUpdateView,
    DistributorAutocomplete,
    SearchParameterAutocomplete,
    ChemicalListUploadView,
    ChemicalListVerifyView,
    ChemicalTableView
)

from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_required(ChemicalListView.as_view()), name='chemmanager-home'),
    path('<int:pk>/', ChemicalListView.as_view(), name='chemical-list'),
    path('chemical/all/', ChemicalTableView.as_view(), name='chemical-table'),
    path('upload/chemicallist/<int:pk>/verify/', ChemicalListVerifyView.as_view(), name='chemicallist-verify'),
    path('upload/chemicallist/', ChemicalListUploadView.as_view(), name="chemicallist-upload"),
    path('chemical/<int:pk>/update', ChemicalUpdateView.as_view(), name='chemical-update'),
    path('chemical/new/', login_required(ChemicalCreateView.as_view()), name='chemical-create'),
    path('chemical/new/<chemical_name>/', login_required(ChemicalCreateView.as_view()),
         name='chemical-create-by-name'),
    path('stock/<int:pk>/new/', login_required(StockCreateView.as_view()), name='stock-create'),
    path('stock/<int:pk>/', login_required(StockUpdateView.as_view()), name='stock-update'),
    path('chemical/<int:pk>/delete', ChemicalDeleteView.as_view(), name='chemical-delete'),
    path('stock/<int:pk>/extraction/new', ExtractionCreateView.as_view(), name='extraction-create'),
    path('stock/<int:pk>/delete', StockDeleteView.as_view(), name='stock-delete'),
    path('storage/', StorageListView.as_view(), name='storage-list'),
    path('storage/<int:pk>/add/', StorageCreateView.as_view(), name='storage-create'),
    path('storage/<int:pk>/update/', StorageUpdateView.as_view(), name='storage-update'),
    path('storage/<int:pk>/delete/', StorageDeleteView.as_view(), name='storage-delete'),
    path('chemical/<int:pk>/', ChemicalDetailView.as_view(), name='chemical-detail'),
    path('distributor-autocomplete/', DistributorAutocomplete.as_view(create_field='name'),
         name='distributor-autocomplete'),
    path('search-parameter-autocomplete/', SearchParameterAutocomplete.as_view(), name='search-parameter-autocomplete'),
]
