from django.urls import re_path
from .views import (
    LoginView,
    CurrentUserView,
    CategoryListCreateView,
    CategoryDetailView,
    ProductListCreateView,
    ProductDetailView,
    IngredientListCreateView,
    IngredientDetailView,
    StockImportView,
    StockMovementListView,
    OrderListCreateView,
    OrderDetailView,
    OrderCheckoutView,
    OrderConfirmView,
    OrderStatusUpdateView,
    DashboardMetricsView,
    SalesReportView,
    AuditLogListView,
    EmployeeListView,
    InventoryStatusView,
    ReportsSummaryView,
)

urlpatterns = [
    # Auth
    re_path(r'^auth/login/?$', LoginView.as_view(), name='auth-login'),
    re_path(r'^auth/me/?$', CurrentUserView.as_view(), name='auth-me'),

    # Categories
    re_path(r'^categories/?$', CategoryListCreateView.as_view(), name='category-list-create'),
    re_path(r'^categories/(?P<pk>\d+)/?$', CategoryDetailView.as_view(), name='category-detail'),

    # Products
    re_path(r'^products/?$', ProductListCreateView.as_view(), name='product-list-create'),
    re_path(r'^products/(?P<pk>\d+)/?$', ProductDetailView.as_view(), name='product-detail'),

    # Ingredients & Inventory (both /ingredients and /inventory/ingredients patterns supported)
    re_path(r'^ingredients/?$', IngredientListCreateView.as_view(), name='ingredient-list-create'),
    re_path(r'^ingredients/(?P<pk>\d+)/?$', IngredientDetailView.as_view(), name='ingredient-detail'),
    re_path(r'^ingredients/import/?$', StockImportView.as_view(), name='ingredient-import'),

    re_path(r'^inventory/ingredients/?$', IngredientListCreateView.as_view(), name='inventory-ingredients'),
    re_path(r'^inventory/ingredients/(?P<pk>\d+)/?$', IngredientDetailView.as_view(), name='inventory-ingredients-detail'),
    re_path(r'^inventory/import/?$', StockImportView.as_view(), name='inventory-import'),
    re_path(r'^inventory/movements/?$', StockMovementListView.as_view(), name='inventory-movements'),

    # Orders & Checkout
    re_path(r'^orders/?$', OrderListCreateView.as_view(), name='order-list-create'),
    re_path(r'^orders/(?P<pk>\d+)/?$', OrderDetailView.as_view(), name='order-detail'),
    re_path(r'^orders/(?P<pk>\d+)/checkout/?$', OrderCheckoutView.as_view(), name='order-checkout'),
    re_path(r'^orders/(?P<pk>\d+)/confirm/?$', OrderConfirmView.as_view(), name='order-confirm'),
    re_path(r'^orders/(?P<pk>\d+)/status/?$', OrderStatusUpdateView.as_view(), name='order-status-update'),

    # Management & Reports
    re_path(r'^management/dashboard/?$', DashboardMetricsView.as_view(), name='management-dashboard'),
    re_path(r'^management/dashboard/metrics/?$', DashboardMetricsView.as_view(), name='management-dashboard-metrics'),
    re_path(r'^management/reports/sales/?$', SalesReportView.as_view(), name='management-reports-sales'),
    re_path(r'^management/audit-logs/?$', AuditLogListView.as_view(), name='management-audit-logs'),
    re_path(r'^management/employees/?$', EmployeeListView.as_view(), name='management-employees'),
    re_path(r'^management/inventory-status/?$', InventoryStatusView.as_view(), name='management-inventory-status'),
    re_path(r'^reports/summary/?$', ReportsSummaryView.as_view(), name='reports-summary'),
]
