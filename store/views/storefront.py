from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.views.decorators.http import require_POST
import json

from ..models import Category, Article, ArticleSize, Order, OrderItem, UserProfile


def home_view(request):
    categories = Category.objects.all()
    selected_category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    
    articles = Article.objects.filter(is_active=True).prefetch_related('images', 'sizes', 'category')
    
    if selected_category_slug:
        articles = articles.filter(category__slug=selected_category_slug)
        
    if search_query:
        articles = articles.filter(title__icontains=search_query) | articles.filter(description__icontains=search_query)

    featured_articles = Article.objects.filter(is_active=True, is_featured=True).prefetch_related('images', 'sizes')[:6]
    
    # Collect all article images for the hero banner slideshow
    from ..models import ArticleImage
    hero_images = list(ArticleImage.objects.filter(
        article__is_active=True
    ).select_related('article').values_list('image', flat=True)[:20])
    
    context = {
        'categories': categories,
        'articles': articles,
        'featured_articles': featured_articles,
        'selected_category_slug': selected_category_slug,
        'search_query': search_query,
        'hero_images': hero_images,
    }
    return render(request, 'store/home.html', context)



def article_detail_view(request, slug):
    article = get_object_or_404(Article.objects.prefetch_related('images', 'sizes', 'category'), slug=slug)
    related_articles = Article.objects.filter(category=article.category, is_active=True).exclude(id=article.id)[:4]
    
    context = {
        'article': article,
        'related_articles': related_articles,
    }
    return render(request, 'store/product_detail.html', context)


def get_cart(request):
    return request.session.get('cart', {})


def save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def cart_detail_view(request):
    cart = get_cart(request)
    cart_items = []
    total_price = 0
    
    for key, item in cart.items():
        article_id = item.get('article_id')
        size_label = item.get('size')
        quantity = item.get('quantity')
        
        try:
            article = Article.objects.get(id=article_id)
            subtotal = article.price * quantity
            total_price += subtotal
            cart_items.append({
                'key': key,
                'article': article,
                'size': size_label,
                'quantity': quantity,
                'subtotal': subtotal,
            })
        except Article.DoesNotExist:
            continue
            
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'store/cart.html', context)


@require_POST
def add_to_cart_api(request):
    try:
        data = json.loads(request.body)
        article_id = data.get('article_id')
        size = data.get('size')
        quantity = int(data.get('quantity', 1))
        
        article = get_object_or_404(Article, id=article_id)
        
        # Check size stock
        size_obj = ArticleSize.objects.filter(article=article, size=size).first()
        if not size_obj or size_obj.stock_quantity < quantity:
            return JsonResponse({'success': False, 'message': f'Sorry, only {size_obj.stock_quantity if size_obj else 0} left in size {size}.'}, status=400)
            
        cart = get_cart(request)
        cart_key = f"{article_id}_{size}"
        
        if cart_key in cart:
            cart[cart_key]['quantity'] += quantity
        else:
            cart[cart_key] = {
                'article_id': article.id,
                'title': article.title,
                'price': str(article.price),
                'size': size,
                'quantity': quantity,
                'image': article.primary_image or '',
            }
            
        save_cart(request, cart)
        total_count = sum(item['quantity'] for item in cart.values())
        return JsonResponse({'success': True, 'cart_count': total_count, 'message': f'Added {article.title} (Size {size}) to cart!'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@require_POST
def update_cart_api(request):
    try:
        data = json.loads(request.body)
        key = data.get('key')
        action = data.get('action') # 'increase', 'decrease', 'remove'
        
        cart = get_cart(request)
        if key in cart:
            if action == 'increase':
                # Check stock
                art_id = cart[key]['article_id']
                sz = cart[key]['size']
                size_obj = ArticleSize.objects.filter(article_id=art_id, size=sz).first()
                if size_obj and cart[key]['quantity'] + 1 > size_obj.stock_quantity:
                    return JsonResponse({'success': False, 'message': f'Cannot add more. Max available stock is {size_obj.stock_quantity}.'}, status=400)
                cart[key]['quantity'] += 1
            elif action == 'decrease':
                cart[key]['quantity'] -= 1
                if cart[key]['quantity'] <= 0:
                    del cart[key]
            elif action == 'remove':
                del cart[key]
                
            save_cart(request, cart)
            
        total_count = sum(item['quantity'] for item in cart.values())
        return JsonResponse({'success': True, 'cart_count': total_count})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def checkout_view(request):
    cart = get_cart(request)
    if not cart:
        messages.warning(request, "Your shopping cart is empty.")
        return redirect('store:home')
        
    cart_items = []
    total_price = 0
    
    for key, item in cart.items():
        article_id = item.get('article_id')
        size_label = item.get('size')
        quantity = item.get('quantity')
        
        try:
            article = Article.objects.get(id=article_id)
            subtotal = article.price * quantity
            total_price += subtotal
            cart_items.append({
                'article': article,
                'size': size_label,
                'quantity': quantity,
                'subtotal': subtotal,
            })
        except Article.DoesNotExist:
            continue

    user_profile = None
    if request.user.is_authenticated:
        user_profile = getattr(request.user, 'profile', None)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'user_profile': user_profile,
    }
    return render(request, 'store/checkout.html', context)


@require_POST
def place_order_view(request):
    cart = get_cart(request)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('store:home')

    # If user is not authenticated, check POST form for login or registration inputs
    if not request.user.is_authenticated:
        auth_action = request.POST.get('auth_action')
        
        if auth_action == 'login':
            email_or_user = request.POST.get('login_username')
            pwd = request.POST.get('login_password')
            user = authenticate(request, username=email_or_user, password=pwd)
            if not user:
                # Try email fallback
                try:
                    user_obj = User.objects.get(email=email_or_user)
                    user = authenticate(request, username=user_obj.username, password=pwd)
                except User.DoesNotExist:
                    pass
                    
            if user:
                login(request, user)
            else:
                messages.error(request, "Invalid login credentials. Please log in or register to complete your purchase.")
                return redirect('store:checkout')
                
        elif auth_action == 'register':
            full_name = request.POST.get('reg_full_name')
            email = request.POST.get('reg_email')
            phone = request.POST.get('reg_phone')
            address = request.POST.get('reg_address')
            city = request.POST.get('reg_city')
            pwd = request.POST.get('reg_password')
            
            if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
                messages.error(request, "An account with this email already exists. Please log in.")
                return redirect('store:checkout')
                
            user = User.objects.create_user(username=email, email=email, password=pwd, first_name=full_name)
            UserProfile.objects.create(
                user=user,
                full_name=full_name,
                phone=phone,
                address=address,
                city=city
            )
            login(request, user)
        else:
            messages.error(request, "Authentication is required at checkout. Please log in or register.")
            return redirect('store:checkout')

    # Retrieve buyer details
    full_name = request.POST.get('full_name') or (request.user.profile.full_name if hasattr(request.user, 'profile') else request.user.get_full_name())
    phone = request.POST.get('phone') or (request.user.profile.phone if hasattr(request.user, 'profile') else '')
    address = request.POST.get('address') or (request.user.profile.address if hasattr(request.user, 'profile') else '')
    city = request.POST.get('city') or (request.user.profile.city if hasattr(request.user, 'profile') else '')
    notes = request.POST.get('notes', '')

    try:
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                client_name=full_name,
                client_phone=phone,
                client_address=address,
                client_city=city,
                source=Order.SOURCE_ONLINE,
                status=Order.STATUS_PENDING,
                notes=notes
            )
            
            total_amount = 0
            for key, item in cart.items():
                article_id = item.get('article_id')
                size_label = item.get('size')
                quantity = item.get('quantity')
                
                article = Article.objects.select_for_update().get(id=article_id)
                size_obj = ArticleSize.objects.select_for_update().get(article=article, size=size_label)
                
                if size_obj.stock_quantity < quantity:
                    raise Exception(f"Insufficient stock for {article.title} (Size {size_label}). Available: {size_obj.stock_quantity}")
                    
                # Decrement stock
                size_obj.stock_quantity -= quantity
                size_obj.save()
                
                item_subtotal = article.price * quantity
                total_amount += item_subtotal
                
                OrderItem.objects.create(
                    order=order,
                    article=article,
                    article_title=article.title,
                    size=size_label,
                    quantity=quantity,
                    unit_price=article.price,
                    subtotal=item_subtotal
                )
                
            order.total_amount = total_amount
            order.save()
            
            # Clear session cart
            request.session['cart'] = {}
            request.session.modified = True
            
            return redirect('store:order_success', order_number=order.order_number)

    except Exception as e:
        messages.error(request, f"Could not process order: {str(e)}")
        return redirect('store:checkout')


def order_success_view(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items'), order_number=order_number)
    context = {
        'order': order,
    }
    return render(request, 'store/order_success.html', context)


def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('store:home')


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('store:admin_dashboard')
        return redirect('store:profile')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        auth_action = request.POST.get('auth_action', 'login')
        if auth_action == 'login':
            email_or_user = request.POST.get('login_username', '').strip()
            pwd = request.POST.get('login_password', '')
            user = authenticate(request, username=email_or_user, password=pwd)
            if not user:
                try:
                    user_obj = User.objects.get(email=email_or_user)
                    user = authenticate(request, username=user_obj.username, password=pwd)
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    pass
            
            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                if user.is_staff:
                    return redirect('store:admin_dashboard')
                return redirect('store:profile')
            else:
                messages.error(request, "Invalid username/email or password.")

        elif auth_action == 'register':
            full_name = request.POST.get('reg_full_name', '').strip()
            email = request.POST.get('reg_email', '').strip()
            phone = request.POST.get('reg_phone', '').strip()
            address = request.POST.get('reg_address', '').strip()
            city = request.POST.get('reg_city', '').strip()
            pwd = request.POST.get('reg_password', '')

            if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
                messages.error(request, "An account with this email already exists. Please sign in.")
            else:
                user = User.objects.create_user(username=email, email=email, password=pwd, first_name=full_name)
                UserProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    phone=phone,
                    address=address,
                    city=city
                )
                login(request, user)
                messages.success(request, "Account created successfully!")
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('store:profile')

    context = {
        'next_url': next_url,
    }
    return render(request, 'store/login.html', context)


def set_language_view(request):
    lang = request.GET.get('lang', 'en')
    if lang in ('en', 'fr', 'ar'):
        request.session['lang'] = lang
    referer = request.META.get('HTTP_REFERER')
    if referer and referer.startswith('http'):
        return redirect(referer)
    return redirect('store:home')
