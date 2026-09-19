from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
import json

from ..models import Category, Article, ArticleImage, ArticleSize, Order, OrderItem, FeaturedShowcase, FeaturedShowcaseItem

STANDARD_SIZES = ['S', 'M', 'L', 'XL', 'XXL', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', 'One Size']

STANDARD_COLORS = [
    # Neutrals & Monochromes
    {'name': 'Black', 'hex': '#0A0A0A', 'border': '#333333', 'family': 'Neutrals'},
    {'name': 'Jet Black', 'hex': '#000000', 'border': '#222222', 'family': 'Neutrals'},
    {'name': 'Charcoal', 'hex': '#374151', 'border': '#4B5563', 'family': 'Neutrals'},
    {'name': 'Anthracite', 'hex': '#27272A', 'border': '#3F3F46', 'family': 'Neutrals'},
    {'name': 'Dark Grey', 'hex': '#4B5563', 'border': '#6B7280', 'family': 'Neutrals'},
    {'name': 'Slate Grey', 'hex': '#64748B', 'border': '#94A3B8', 'family': 'Neutrals'},
    {'name': 'Grey', 'hex': '#6B7280', 'border': '#9CA3AF', 'family': 'Neutrals'},
    {'name': 'Heather Grey', 'hex': '#9CA3AF', 'border': '#CBD5E1', 'family': 'Neutrals'},
    {'name': 'Light Grey', 'hex': '#D1D5DB', 'border': '#9CA3AF', 'family': 'Neutrals'},
    {'name': 'Silver', 'hex': '#E2E8F0', 'border': '#CBD5E1', 'family': 'Neutrals'},
    {'name': 'Ash', 'hex': '#B0BEC5', 'border': '#CFD8DC', 'family': 'Neutrals'},
    {'name': 'White', 'hex': '#FFFFFF', 'border': '#D1D5DB', 'family': 'Neutrals'},
    {'name': 'Off-White', 'hex': '#FAF9F6', 'border': '#D1D5DB', 'family': 'Neutrals'},
    {'name': 'Snow White', 'hex': '#F8FAFC', 'border': '#E2E8F0', 'family': 'Neutrals'},
    {'name': 'Cream', 'hex': '#FDFBF7', 'border': '#E5E7EB', 'family': 'Neutrals'},
    {'name': 'Ivory', 'hex': '#FFFFF0', 'border': '#E5E7EB', 'family': 'Neutrals'},
    {'name': 'Ecru', 'hex': '#F5F5DC', 'border': '#D6D3D1', 'family': 'Neutrals'},
    {'name': 'Bone', 'hex': '#E5E5E0', 'border': '#D1D5DB', 'family': 'Neutrals'},

    # Blues & Navies
    {'name': 'Navy', 'hex': '#1E293B', 'border': '#334155', 'family': 'Blues'},
    {'name': 'Midnight Blue', 'hex': '#0F172A', 'border': '#1E293B', 'family': 'Blues'},
    {'name': 'Deep Navy', 'hex': '#0A1128', 'border': '#1C2541', 'family': 'Blues'},
    {'name': 'Indigo', 'hex': '#4338CA', 'border': '#4F46E5', 'family': 'Blues'},
    {'name': 'Royal Blue', 'hex': '#1D4ED8', 'border': '#2563EB', 'family': 'Blues'},
    {'name': 'Cobalt', 'hex': '#2563EB', 'border': '#3B82F6', 'family': 'Blues'},
    {'name': 'Ocean Blue', 'hex': '#0284C7', 'border': '#0EA5E9', 'family': 'Blues'},
    {'name': 'Denim', 'hex': '#3B82F6', 'border': '#60A5FA', 'family': 'Blues'},
    {'name': 'Steel Blue', 'hex': '#4682B4', 'border': '#5C93C4', 'family': 'Blues'},
    {'name': 'Slate Blue', 'hex': '#60A5FA', 'border': '#93C5FD', 'family': 'Blues'},
    {'name': 'Sky Blue', 'hex': '#7DD3FC', 'border': '#38BDF8', 'family': 'Blues'},
    {'name': 'Light Blue', 'hex': '#BAE6FD', 'border': '#7DD3FC', 'family': 'Blues'},
    {'name': 'Baby Blue', 'hex': '#E0F2FE', 'border': '#BAE6FD', 'family': 'Blues'},
    {'name': 'Teal', 'hex': '#0D9488', 'border': '#14B8A6', 'family': 'Blues'},
    {'name': 'Turquoise', 'hex': '#06B6D4', 'border': '#22D3EE', 'family': 'Blues'},
    {'name': 'Cyan', 'hex': '#0891B2', 'border': '#06B6D4', 'family': 'Blues'},

    # Earth, Browns & Warm Neutrals
    {'name': 'Beige', 'hex': '#D4B996', 'border': '#E5D5C5', 'family': 'Earth Tones'},
    {'name': 'Sand', 'hex': '#E6D5B8', 'border': '#CBB799', 'family': 'Earth Tones'},
    {'name': 'Oatmeal', 'hex': '#D6CFC7', 'border': '#C4BCB3', 'family': 'Earth Tones'},
    {'name': 'Stone', 'hex': '#C4B5A5', 'border': '#A89989', 'family': 'Earth Tones'},
    {'name': 'Tan', 'hex': '#D2B48C', 'border': '#C4A47C', 'family': 'Earth Tones'},
    {'name': 'Camel', 'hex': '#C19A6B', 'border': '#D2B48C', 'family': 'Earth Tones'},
    {'name': 'Taupe', 'hex': '#8B8589', 'border': '#A29D9D', 'family': 'Earth Tones'},
    {'name': 'Khaki', 'hex': '#656D4A', 'border': '#7F8960', 'family': 'Earth Tones'},
    {'name': 'Brown', 'hex': '#78350F', 'border': '#92400E', 'family': 'Earth Tones'},
    {'name': 'Dark Brown', 'hex': '#451A03', 'border': '#78350F', 'family': 'Earth Tones'},
    {'name': 'Mocha', 'hex': '#6F4E37', 'border': '#855E42', 'family': 'Earth Tones'},
    {'name': 'Chocolate', 'hex': '#3E2723', 'border': '#5D4037', 'family': 'Earth Tones'},
    {'name': 'Cognac', 'hex': '#9A3412', 'border': '#C2410C', 'family': 'Earth Tones'},
    {'name': 'Bronze', 'hex': '#CD7F32', 'border': '#B86F28', 'family': 'Earth Tones'},
    {'name': 'Rust', 'hex': '#B45309', 'border': '#D97706', 'family': 'Earth Tones'},
    {'name': 'Amber', 'hex': '#D97706', 'border': '#F59E0B', 'family': 'Earth Tones'},
    {'name': 'Mustard', 'hex': '#EAB308', 'border': '#FACC15', 'family': 'Earth Tones'},
    {'name': 'Ochre', 'hex': '#CC7722', 'border': '#E08B38', 'family': 'Earth Tones'},
    {'name': 'Gold', 'hex': '#D4AF37', 'border': '#F3E5AB', 'family': 'Earth Tones'},

    # Greens & Olives
    {'name': 'Olive', 'hex': '#556B2F', 'border': '#6B8E23', 'family': 'Greens'},
    {'name': 'Olive Drab', 'hex': '#4B5320', 'border': '#5E6729', 'family': 'Greens'},
    {'name': 'Military Green', 'hex': '#3E4E38', 'border': '#52664B', 'family': 'Greens'},
    {'name': 'Forest Green', 'hex': '#14532D', 'border': '#15803D', 'family': 'Greens'},
    {'name': 'Pine Green', 'hex': '#064E3B', 'border': '#047857', 'family': 'Greens'},
    {'name': 'Bottle Green', 'hex': '#0F382A', 'border': '#1A5943', 'family': 'Greens'},
    {'name': 'Hunter Green', 'hex': '#355E3B', 'border': '#467B4E', 'family': 'Greens'},
    {'name': 'Sage Green', 'hex': '#9CAF88', 'border': '#7D9B76', 'family': 'Greens'},
    {'name': 'Moss Green', 'hex': '#8A9A5B', 'border': '#9EB06D', 'family': 'Greens'},
    {'name': 'Emerald', 'hex': '#047857', 'border': '#059669', 'family': 'Greens'},
    {'name': 'Mint', 'hex': '#6EE7B7', 'border': '#34D399', 'family': 'Greens'},
    {'name': 'Seafoam', 'hex': '#A7F3D0', 'border': '#6EE7B7', 'family': 'Greens'},
    {'name': 'Pistachio', 'hex': '#93C572', 'border': '#7FB35D', 'family': 'Greens'},

    # Reds, Burgundies & Warm Accents
    {'name': 'Burgundy', 'hex': '#800020', 'border': '#9B111E', 'family': 'Reds'},
    {'name': 'Bordeaux', 'hex': '#581C87', 'border': '#7E22CE', 'family': 'Reds'},
    {'name': 'Wine', 'hex': '#722F37', 'border': '#8C3B45', 'family': 'Reds'},
    {'name': 'Maroon', 'hex': '#800000', 'border': '#9C1C1C', 'family': 'Reds'},
    {'name': 'Crimson', 'hex': '#991B1B', 'border': '#B91C1C', 'family': 'Reds'},
    {'name': 'Red', 'hex': '#DC2626', 'border': '#EF4444', 'family': 'Reds'},
    {'name': 'Ruby', 'hex': '#BE123C', 'border': '#E11D48', 'family': 'Reds'},
    {'name': 'Brick Red', 'hex': '#B91C1C', 'border': '#DC2626', 'family': 'Reds'},
    {'name': 'Terracotta', 'hex': '#C2410C', 'border': '#EA580C', 'family': 'Reds'},
    {'name': 'Coral', 'hex': '#F87171', 'border': '#EF4444', 'family': 'Reds'},
    {'name': 'Salmon', 'hex': '#FB7185', 'border': '#F43F5E', 'family': 'Reds'},
    {'name': 'Peach', 'hex': '#FB923C', 'border': '#F97316', 'family': 'Reds'},
    {'name': 'Orange', 'hex': '#EA580C', 'border': '#F97316', 'family': 'Reds'},
    {'name': 'Burnt Orange', 'hex': '#C2410C', 'border': '#EA580C', 'family': 'Reds'},

    # Pinks, Purples & Pastels
    {'name': 'Dusty Rose', 'hex': '#FDA4AF', 'border': '#FB7185', 'family': 'Pinks & Purples'},
    {'name': 'Blush', 'hex': '#FFE4E6', 'border': '#FDA4AF', 'family': 'Pinks & Purples'},
    {'name': 'Rose', 'hex': '#F43F5E', 'border': '#FB7185', 'family': 'Pinks & Purples'},
    {'name': 'Light Pink', 'hex': '#FBCFE8', 'border': '#F472B6', 'family': 'Pinks & Purples'},
    {'name': 'Magenta', 'hex': '#DB2777', 'border': '#EC4899', 'family': 'Pinks & Purples'},
    {'name': 'Plum', 'hex': '#4A044E', 'border': '#701A75', 'family': 'Pinks & Purples'},
    {'name': 'Eggplant', 'hex': '#3B0764', 'border': '#581C87', 'family': 'Pinks & Purples'},
    {'name': 'Lavender', 'hex': '#C084FC', 'border': '#A855F7', 'family': 'Pinks & Purples'},
    {'name': 'Lilac', 'hex': '#E9D5FF', 'border': '#C084FC', 'family': 'Pinks & Purples'},
    {'name': 'Violet', 'hex': '#7C3AED', 'border': '#8B5CF6', 'family': 'Pinks & Purples'},
    {'name': 'Mauve', 'hex': '#B784A7', 'border': '#C99EBC', 'family': 'Pinks & Purples'},
]


def _parse_variant_rows(request):
    sizes_data = request.POST.getlist('size_name')
    colors_data = request.POST.getlist('color_name')
    stock_data = request.POST.getlist('size_stock')

    if len(colors_data) < len(sizes_data):
        colors_data += [''] * (len(sizes_data) - len(colors_data))

    variants = []
    for index, (size, color, stock) in enumerate(zip(sizes_data, colors_data, stock_data), start=1):
        size_clean = (size or '').strip()
        color_clean = (color or '').strip()
        stock_clean = (stock or '').strip()

        if not size_clean:
            continue
        try:
            stock_quantity = int(stock_clean)
        except (TypeError, ValueError):
            raise ValueError(
                f'Variant {index} ({color_clean or size_clean}) must have a whole-number stock quantity.'
            )
        if stock_quantity < 0:
            raise ValueError(f'Variant {index} ({color_clean or size_clean}) cannot have negative stock.')

        variants.append((size_clean, color_clean, stock_quantity))

    return variants

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
            'has_colors': art.has_colors,
            'colors': art.available_colors,
            'sizes': [
                {'size': s.size, 'color': s.color or '', 'stock': s.stock_quantity}
                for s in art.sizes.all()
            ]
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
                client_address='In-Store Walk-In (Casablanca)',
                client_city='Casablanca',
                source=Order.SOURCE_IN_STORE,
                status=Order.STATUS_DELIVERED,
                notes=notes
            )
            
            total_amount = 0
            for item in items:
                article_id = item['article_id']
                size_label = item['size']
                color_label = item.get('color', '').strip()
                try:
                    quantity = int(item.get('quantity', 1))
                except (TypeError, ValueError):
                    return JsonResponse({
                        'success': False,
                        'message': 'Quantity must be a whole number. Color values must be sent in the color field.'
                    }, status=400)
                if quantity < 1:
                    return JsonResponse({
                        'success': False,
                        'message': 'Quantity must be at least 1.'
                    }, status=400)
                
                article = Article.objects.select_for_update().get(id=article_id)
                if color_label:
                    size_obj = ArticleSize.objects.select_for_update().filter(article=article, size=size_label, color=color_label).first()
                else:
                    size_obj = ArticleSize.objects.select_for_update().filter(article=article, size=size_label).first()
                
                if not size_obj:
                    variant_desc = f"Size {size_label}" + (f" / Color {color_label}" if color_label else "")
                    raise Exception(f"Variant {variant_desc} not found for {article.title}")
                    
                if size_obj.stock_quantity < quantity:
                    variant_desc = f"Size {size_label}" + (f" / Color {color_label}" if color_label else "")
                    raise Exception(f"Insufficient stock for {article.title} ({variant_desc}). Available stock: {size_obj.stock_quantity}")
                    
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
                    color=color_label,
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
    
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        
        category = get_object_or_404(Category, id=category_id)
        try:
            variants = _parse_variant_rows(request)
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, 'admin_panel/article_form.html', {
                'categories': categories,
                'standard_sizes': STANDARD_SIZES,
                'standard_colors': STANDARD_COLORS,
                'title': 'Add New Article',
            })
        
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
                
            # Handle stock sizes & colors
            for size, color, stock_quantity in variants:
                ArticleSize.objects.create(
                    article=article,
                    size=size,
                    color=color,
                    stock_quantity=stock_quantity
                )
                    
            messages.success(request, f"Article '{article.title}' created successfully.")
            return redirect('store:admin_articles')
            
    context = {
        'categories': categories,
        'standard_sizes': STANDARD_SIZES,
        'standard_colors': STANDARD_COLORS,
        'title': 'Add New Article',
    }
    return render(request, 'admin_panel/article_form.html', context)


@staff_member_required
def article_edit_view(request, article_id):
    article = get_object_or_404(Article.objects.prefetch_related('sizes', 'images'), id=article_id)
    categories = Category.objects.all()
    pass
    
    if request.method == 'POST':
        try:
            variants = _parse_variant_rows(request)
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, 'admin_panel/article_form.html', {
                'article': article,
                'categories': categories,
                'standard_sizes': STANDARD_SIZES,
                'standard_colors': STANDARD_COLORS,
                'title': f'Edit Article: {article.title}',
            })

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
            
        # Update sizes & colors
        article.sizes.all().delete()
        for size, color, stock_quantity in variants:
            ArticleSize.objects.create(
                article=article,
                size=size,
                color=color,
                stock_quantity=stock_quantity
            )
                
        messages.success(request, f"Article '{article.title}' updated.")
        return redirect('store:admin_articles')
        
    context = {
        'article': article,
        'categories': categories,
        'standard_sizes': STANDARD_SIZES,
        'standard_colors': STANDARD_COLORS,
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


# ==========================================
# CRUD Views for Featured Showcases (Outfits)
# ==========================================

@staff_member_required
def showcases_list_view(request):
    search_query = request.GET.get('q', '').strip()
    showcases = FeaturedShowcase.objects.annotate(
        items_count=Count('items')
    ).prefetch_related('items__article').all()

    if search_query:
        showcases = showcases.filter(title__icontains=search_query) | showcases.filter(description__icontains=search_query)

    context = {
        'showcases': showcases,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/showcases_list.html', context)


@staff_member_required
def showcase_create_view(request):
    all_articles = Article.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'sizes').order_by('category__name', 'title')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        cover_image = request.FILES.get('cover_image')
        is_active = request.POST.get('is_active') == 'on'

        if not title:
            messages.error(request, "Showcase title is required.")
        else:
            with transaction.atomic():
                showcase = FeaturedShowcase.objects.create(
                    title=title,
                    description=description,
                    cover_image=cover_image,
                    is_active=is_active
                )

                # Process attached articles and orders
                article_ids = request.POST.getlist('article_ids')
                display_orders = request.POST.getlist('display_orders')

                added_articles = set()
                for idx, art_id in enumerate(article_ids):
                    if art_id and art_id not in added_articles:
                        try:
                            article = Article.objects.get(id=art_id)
                            order_val = int(display_orders[idx]) if idx < len(display_orders) and display_orders[idx].isdigit() else idx + 1
                            FeaturedShowcaseItem.objects.create(
                                showcase=showcase,
                                article=article,
                                display_order=order_val
                            )
                            added_articles.add(art_id)
                        except Article.DoesNotExist:
                            continue

                messages.success(request, f"Featured Showcase '{showcase.title}' created with {len(added_articles)} articles.")
                return redirect('store:admin_showcases')

    context = {
        'title': 'Create Featured Showcase',
        'all_articles': all_articles,
        'selected_items': [],
    }
    return render(request, 'admin_panel/showcase_form.html', context)


@staff_member_required
def showcase_edit_view(request, showcase_id):
    showcase = get_object_or_404(FeaturedShowcase.objects.prefetch_related('items__article__images', 'items__article__category'), id=showcase_id)
    all_articles = Article.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'sizes').order_by('category__name', 'title')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        cover_image = request.FILES.get('cover_image')
        is_active = request.POST.get('is_active') == 'on'

        if not title:
            messages.error(request, "Showcase title is required.")
        else:
            with transaction.atomic():
                showcase.title = title
                showcase.description = description
                showcase.is_active = is_active
                if cover_image:
                    showcase.cover_image = cover_image
                showcase.save()

                # Sync items
                showcase.items.all().delete()
                article_ids = request.POST.getlist('article_ids')
                display_orders = request.POST.getlist('display_orders')

                added_articles = set()
                for idx, art_id in enumerate(article_ids):
                    if art_id and art_id not in added_articles:
                        try:
                            article = Article.objects.get(id=art_id)
                            order_val = int(display_orders[idx]) if idx < len(display_orders) and display_orders[idx].isdigit() else idx + 1
                            FeaturedShowcaseItem.objects.create(
                                showcase=showcase,
                                article=article,
                                display_order=order_val
                            )
                            added_articles.add(art_id)
                        except Article.DoesNotExist:
                            continue

                messages.success(request, f"Showcase '{showcase.title}' updated successfully.")
                return redirect('store:admin_showcases')

    selected_items = showcase.items.select_related('article__category').prefetch_related('article__images', 'article__sizes').all()
    context = {
        'title': f"Edit Showcase: {showcase.title}",
        'showcase': showcase,
        'all_articles': all_articles,
        'selected_items': selected_items,
    }
    return render(request, 'admin_panel/showcase_form.html', context)


@staff_member_required
def showcase_delete_view(request, showcase_id):
    showcase = get_object_or_404(FeaturedShowcase, id=showcase_id)
    if request.method == 'POST':
        title = showcase.title
        showcase.delete()
        messages.success(request, f"Showcase '{title}' deleted.")
        return redirect('store:admin_showcases')
    return render(request, 'admin_panel/confirm_delete.html', {'item_type': 'Featured Showcase', 'item_name': showcase.title})


@staff_member_required
def toggle_showcase_status_api(request, showcase_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)
    try:
        showcase = get_object_or_404(FeaturedShowcase, id=showcase_id)
        showcase.is_active = not showcase.is_active
        showcase.save(update_fields=['is_active'])
        return JsonResponse({
            'success': True,
            'is_active': showcase.is_active,
            'message': f"Showcase is now {'active' if showcase.is_active else 'inactive'}."
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

