from django.urls import path
from .views import storefront, admin_panel, client_profile

app_name = 'store'

urlpatterns = [
    # Storefront Routes
    path('', storefront.home_view, name='home'),
    path('article/<slug:slug>/', storefront.article_detail_view, name='product_detail'),
    path('cart/', storefront.cart_detail_view, name='cart_detail'),
    path('checkout/', storefront.checkout_view, name='checkout'),
    path('place-order/', storefront.place_order_view, name='place_order'),
    path('order-success/<str:order_number>/', storefront.order_success_view, name='order_success'),
    path('login/', storefront.login_view, name='login'),
    path('logout/', storefront.logout_user, name='logout'),
    path('set-language/', storefront.set_language_view, name='set_language'),
    
    # Storefront Cart APIs
    path('api/cart/add/', storefront.add_to_cart_api, name='api_cart_add'),
    path('api/cart/update/', storefront.update_cart_api, name='api_cart_update'),
    
    # Client Profile & Orders
    path('profile/', client_profile.profile_view, name='profile'),
    
    # Admin Dashboard Routes
    path('admin-dashboard/', admin_panel.dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/api/sales-chart/', admin_panel.sales_chart_data_api, name='admin_sales_chart_api'),
    path('admin-dashboard/pos/', admin_panel.pos_sale_view, name='admin_pos'),
    path('admin-dashboard/pos/process/', admin_panel.process_pos_sale_api, name='admin_pos_process'),
    path('admin-dashboard/orders/', admin_panel.orders_list_view, name='admin_orders'),
    path('admin-dashboard/orders/<int:order_id>/status/', admin_panel.update_order_status_api, name='admin_order_status_update'),
    
    # Admin Category CRUD
    path('admin-dashboard/categories/', admin_panel.categories_list_view, name='admin_categories'),
    path('admin-dashboard/categories/add/', admin_panel.category_create_view, name='admin_category_create'),
    path('admin-dashboard/categories/<int:category_id>/edit/', admin_panel.category_edit_view, name='admin_category_edit'),
    path('admin-dashboard/categories/<int:category_id>/delete/', admin_panel.category_delete_view, name='admin_category_delete'),
    
    # Admin Article CRUD
    path('admin-dashboard/articles/', admin_panel.articles_list_view, name='admin_articles'),
    path('admin-dashboard/articles/add/', admin_panel.article_create_view, name='admin_article_create'),
    path('admin-dashboard/articles/<int:article_id>/edit/', admin_panel.article_edit_view, name='admin_article_edit'),
    path('admin-dashboard/articles/<int:article_id>/delete/', admin_panel.article_delete_view, name='admin_article_delete'),
]
