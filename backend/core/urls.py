from django.urls import path

from . import views


urlpatterns = [
    path('auth/signup/', views.UserSignupView.as_view(), name='user-signup'),
    path('orders/', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('quotes/calculate/', views.CalculateQuoteView.as_view(), name='quote-calculate'),
    path('items/', views.ItemListCreateView.as_view(), name='item-list-create'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),
    path('items/<int:pk>/start/', views.start_item_processing, name='item-start'),
]
