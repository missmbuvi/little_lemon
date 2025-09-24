from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.index, name='api-home'),
    path('categories/', views.CategoryView.as_view(), name='categories'),
    path('menu-items/', views.MenuItemView.as_view(), name='menu-items'),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view(), name='single-menu-item'),
    path('cart/menu-items/', views.CartView.as_view(), name='cart'),
    path('orders/', views.OrderView.as_view(), name='orders'),
    path('orders/<int:pk>', views.SingleOrderView.as_view(), name='single-order'),
    path('groups/manager/users/', views.ManagerGroupView.as_view(), name='manager-group'),
    path('groups/delivery-crew/users/', views.DeliveryCrewGroupView.as_view(), name='delivery-group'),
    path('api/managers/', views.managers),
    path('api/delivery-crew/', views.delivery_crew),
    path('api/users/register/', views.UserCreateView.as_view()),
    
 ]
    
    

