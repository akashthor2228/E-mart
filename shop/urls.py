from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),

    # Collections
    path('collections/', views.product_page, name='collections'),
    path('collections/<str:name>/', views.colectionsview, name='colectionsview'),       # ← renamed + slash
    path('collections/<str:cname>/<str:pname>/', views.product_details, name='product_details'),  # ← slash

    # Cart
    path('addtocart/', views.add_to_cart, name='addtocart'),
    path('cart/', views.cart_page, name='cart'),
    path('remove_cart/<str:cid>/', views.remove_cart, name='remove_cart'),

    # Favourites
    path('fav/', views.fav_page, name='fav'),
    path('remove_fav/<str:cid>/', views.remove_fav, name='remove_fav'),
    path('addtofav/', views.add_to_fav, name='add_to_fav'),

    # Checkout & Payment
    path('checkout/', views.checkout, name='checkout'),
    path('create-order/', views.create_order, name='create_order'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('order-success/', views.order_success, name='order_success'),
]