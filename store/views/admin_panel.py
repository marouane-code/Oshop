from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
import json

from ..models import Category, Article, ArticleImage, ArticleSize, Order, OrderItem

@staff_member_required
def dashboard_view(request):
    time_filter = request.GET.get('filter', 'all') # 'today', 'week', 'month', 'all'
    
    now = timezone.now()
    orders_qs = Order.objects.exclude(status=Order.STATUS_CANCELLED)
    
    if time_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start_date)
    elif time_filter == 'week':
        start_date = now - timedelta(days=7)
        orders_qs = orders_qs.filter(created_at__gte=start_date)
    elif time_filter == 'month':
        start_date = now - timedelta(days=30)
        orders_qs = orders_qs.filter(created_at__gte=start_date)
        
    total_revenue = orders_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    total_orders = orders_qs.count()
    
    # Items sold count
    items_sold = OrderItem.objects.filter(order__in=orders_qs).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Best-selling articles
    best_articles = OrderItem.objects.filter(order__in=orders_qs)\
        .values('article_title')\
        .annotate(total_qty=Sum('quantity'), total_sales=Sum('subtotal'))\
        .order_by('-total_qty')[:5]
        
    # Low stock alerts (stock <= 3)
    low_stock_items = ArticleSize.objects.filter(stock_quantity__lte=3).select_related('article')[:10]
    
    context = {
        'time_filter': time_filter,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'items_sold': items_sold,
        'best_articles': best_articles,
        'low_stock_items': low_stock_items,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@staff_member_required
def sales_chart_data_api(request):
    days = 14
    now = timezone.now()
    labels = []
    revenue_data = []
    orders_data = []
    
    for i in range(days - 1, -1, -1):
        day_date = (now - timedelta(days=i)).date()
        labels.append(day_date.strftime('%b %d'))
        
        day_orders = Order.objects.exclude(status=Order.STATUS_CANCELLED).filter(
            created_at__date=day_date
        )
        day_revenue = day_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_data.append(float(day_revenue))
        orders_data.append(day_orders.count())
        
    return JsonResponse({
        'labels': labels,
        'revenue': revenue_data,
        'orders': orders_data,
    })


@staff_member_required
def pos_sale_view(request):
    articles = Article.objects.filter(is_active=True).prefetch_related('sizes', 'images')
    categories = Category.objects.all()
    
    articles_data = []
    for art in articles:
        articles_data.append({
            'id': art.id,
            'title': art.title,
            'category': art.category.name,
            'price': float(art.price),
            'image': art.primary_image or '',
            'sizes': [{'size': s.size, 'stock': s.stock_quantity} for s in art.sizes.all()]
        })
        
    context = {
        'articles': articles,
        'categories': categories,
        'articles_json': json.dumps(articles_data),
    }
    return render(request, 'admin_panel/pos_sale.html', context)


@staff_member_required
def process_pos_sale_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
        
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        notes = data.get('notes', 'In-Store POS Sale')
        
        if not items:
            return JsonResponse({'success': False, 'message': 'No items selected for sale.'}, status=400)
            
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                client_name='In-Store Customer',
                client_phone='N/A',
                client_address='In-Store Walk-In (Safi)',
                client_city='Safi',
                source=Order.SOURCE_IN_STORE,
                status=Order.STATUS_DELIVERED,
                notes=notes
            )
            
            total_amount = 0
            for item in items:
                article_id = item['article_id']
                size_label = item['size']
                quantity = int(item['quantity'])
                
                article = Article.objects.select_for_update().get(id=article_id)
                size_obj = ArticleSize.objects.select_for_update().get(article=article, size=size_label)
                
                if size_obj.stock_quantity < quantity:
                    raise Exception(f"Insufficient stock for {article.title} (Size {size_label}). Available stock: {size_obj.stock_quantity}")
                    
                # Decrement stock
                size_obj.stock_quantity -= quantity
                size_obj.save()
                
                subtotal = article.price * quantity
                total_amount += subtotal
                
                OrderItem.objects.create(
                    order=order,
                    article=article,
                    article_title=article.title,
                    size=size_label,
                    quantity=quantity,
                    unit_price=article.price,
                    subtotal=subtotal
                )
                
            order.total_amount = total_amount
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'In-store sale #{order.order_number} completed successfully!',
                'order_number': order.order_number,
                'total_amount': float(order.total_amount)
            })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@staff_member_required
def orders_list_view(request):
    source_filter = request.GET.get('source') # 'ONLINE', 'IN_STORE'
    status_filter = request.GET.get('status')
    search_query = request.GET.get('q')
    
    orders = Order.objects.prefetch_related('items').all()
    
    if source_filter:
        orders = orders.filter(source=source_filter)
    if status_filter:
        orders = orders.filter(status=status_filter)
    if search_query:
        orders = orders.filter(order_number__icontains=search_query) | \
                 orders.filter(client_name__icontains=search_query) | \
                 orders.filter(client_phone__icontains=search_query)
                 
    context = {
        'orders': orders,
        'source_filter': source_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/orders_list.html', context)


@staff_member_required
def update_order_status_api(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)
        
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        valid_statuses = dict(Order.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Invalid status choice'}, status=400)
            
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()
        
        return JsonResponse({'success': True, 'message': f'Order {order.order_number} status updated to {order.get_status_display()}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# CRUD Views for Categories
@staff_member_required
def categories_list_view(request):
    categories = Category.objects.annotate(articles_count=Count('articles')).all()
    return render(request, 'admin_panel/categories_list.html', {'categories': categories})


@staff_member_required
def category_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        cover_image = request.FILES.get('cover_image')
        
        if not name:
            messages.error(request, "Category name is required.")
        else:
            category = Category.objects.create(name=name, description=description, cover_image=cover_image)
            messages.success(request, f"Category '{category.name}' created successfully.")
            return redirect('store:admin_categories')
            
    return render(request, 'admin_panel/category_form.html', {'title': 'Add New Category'})


@staff_member_required
def category_edit_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        cover_image = request.FILES.get('cover_image')
        
        if name:
            category.name = name
            category.description = description
            if cover_image:
                category.cover_image = cover_image
            category.save()
            messages.success(request, f"Category '{category.name}' updated.")
            return redirect('store:admin_categories')
            
    return render(request, 'admin_panel/category_form.html', {'category': category, 'title': f'Edit Category: {category.name}'})


@staff_member_required
def category_delete_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted.")
        return redirect('store:admin_categories')
    return render(request, 'admin_panel/confirm_delete.html', {'item_type': 'Category', 'item_name': category.name})


# CRUD Views for Articles
@staff_member_required
def articles_list_view(request):
    articles = Article.objects.select_related('category').prefetch_related('sizes', 'images').all()
    return render(request, 'admin_panel/articles_list.html', {'articles': articles})


@staff_member_required
def article_create_view(request):
    categories = Category.objects.all()
    standard_sizes = ['S', 'M', 'L', 'XL', 'XXL', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45']
    
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        
        category = get_object_or_404(Category, id=category_id)
        
        with transaction.atomic():
            article = Article.objects.create(
                title=title,
                category=category,
                price=price,
                description=description,
                is_active=is_active,
                is_featured=is_featured
            )
            
            # Handle images
            images = request.FILES.getlist('images')
            for index, img_file in enumerate(images):
                ArticleImage.objects.create(
                    article=article,
                    image=img_file,
                    is_primary=(index == 0)
                )
                
            # Handle stock sizes
            sizes_data = request.POST.getlist('size_name')
            stock_data = request.POST.getlist('size_stock')
            
            for sz, qty in zip(sizes_data, stock_data):
                if sz and qty and int(qty) >= 0:
                    ArticleSize.objects.create(
                        article=article,
                        size=sz.strip(),
                        stock_quantity=int(qty)
                    )
                    
            messages.success(request, f"Article '{article.title}' created successfully.")
            return redirect('store:admin_articles')
            
    context = {
        'categories': categories,
        'standard_sizes': standard_sizes,
        'title': 'Add New Article',
    }
    return render(request, 'admin_panel/article_form.html', context)


@staff_member_required
def article_edit_view(request, article_id):
    article = get_object_or_404(Article.objects.prefetch_related('sizes', 'images'), id=article_id)
    categories = Category.objects.all()
    standard_sizes = ['S', 'M', 'L', 'XL', 'XXL', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45']
    
    if request.method == 'POST':
        article.title = request.POST.get('title')
        article.category = get_object_or_404(Category, id=request.POST.get('category'))
        article.price = request.POST.get('price')
        article.description = request.POST.get('description', '')
        article.is_active = request.POST.get('is_active') == 'on'
        article.is_featured = request.POST.get('is_featured') == 'on'
        article.save()
        
        # New images
        images = request.FILES.getlist('images')
        for index, img_file in enumerate(images):
            has_primary = article.images.filter(is_primary=True).exists()
            ArticleImage.objects.create(
                article=article,
                image=img_file,
                is_primary=(not has_primary and index == 0)
            )
            
        # Update sizes
        article.sizes.all().delete()
        sizes_data = request.POST.getlist('size_name')
        stock_data = request.POST.getlist('size_stock')
        
        for sz, qty in zip(sizes_data, stock_data):
            if sz and qty and int(qty) >= 0:
                ArticleSize.objects.create(
                    article=article,
                    size=sz.strip(),
                    stock_quantity=int(qty)
                )
                
        messages.success(request, f"Article '{article.title}' updated.")
        return redirect('store:admin_articles')
        
    context = {
        'article': article,
        'categories': categories,
        'standard_sizes': standard_sizes,
        'title': f'Edit Article: {article.title}',
    }
    return render(request, 'admin_panel/article_form.html', context)


@staff_member_required
def article_delete_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        title = article.title
        article.delete()
        messages.success(request, f"Article '{title}' deleted.")
        return redirect('store:admin_articles')
    return render(request, 'admin_panel/confirm_delete.html', {'item_type': 'Article', 'item_name': article.title})
