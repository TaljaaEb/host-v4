from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:category_slug>/', views.product_list,
         name='product_list_by_category'),
    path('product/<slug:slug>/', views.product_detail,
         name='product_detail'),
    path('search/', views.search, name='search'),

    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove,
         name='cart_remove'),

    path('checkout/', views.checkout, name='checkout'),
    path('payment/<int:order_id>/', views.payment, name='payment'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation,
         name='order_confirmation'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),

    path('like/<int:product_id>/', views.like_product, name='like_product'),

    path('trigger-proc', views.trigger_proc, name='trigger_proc'),
    path('check-trigger', views.check_trigger, name='check_trigger'),
    path('get-hash', views.get_hash, name='get_hash'),
    path('itemlines/<str:md4_hash>', views.get_itemlines, name='get_itemlines'),
]
