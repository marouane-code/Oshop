from django.contrib import admin
from .models import Category, Article, ArticleImage, ArticleSize, UserProfile, Order, OrderItem

class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 1

class ArticleSizeInline(admin.TabularInline):
    model = ArticleSize
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'is_active', 'is_featured', 'total_stock', 'created_at')
    list_filter = ('category', 'is_active', 'is_featured')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ArticleImageInline, ArticleSizeInline]

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone', 'city', 'created_at')
    search_fields = ('full_name', 'phone', 'city', 'user__email')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('subtotal',)
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'client_name', 'client_phone', 'source', 'status', 'total_amount', 'created_at')
    list_filter = ('source', 'status', 'created_at')
    search_fields = ('order_number', 'client_name', 'client_phone', 'client_city')
    inlines = [OrderItemInline]
