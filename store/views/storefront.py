from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Prefetch
from django.contrib import messages
from django.views.decorators.http import require_POST
import json

from ..models import (
    Category,
    Article,
    ArticleImage,
    ArticleSize,
    Order,
    OrderItem,
    UserProfile,
    FeaturedShowcase,
    FeaturedShowcaseItem,
)


HERO_SLIDE_LIMIT = 6


def get_hero_slides():
    articles = (
        Article.objects.filter(
            is_active=True,
            images__image__isnull=False,
            images__image__gt='',
        )
        .select_related('category')
        .prefetch_related(
            Prefetch(
                'images',
                queryset=ArticleImage.objects.order_by('display_order', '-is_primary', 'created_at'),
            )
        )
        .distinct()
        .order_by('-created_at')[:HERO_SLIDE_LIMIT]
    )

    slides = []
    for article in articles:
        for image in article.images.all():
            if not image.image:
                continue
            slides.append({
                'id': image.id,
                'article_id': article.id,
                'image_url': image.image.url,
                'title': article.title,
                'category': article.category.name,
                'price': str(article.price),
                'url': reverse('store:product_detail', args=[article.slug]),
                'updated_at': article.updated_at.isoformat(),
            })
            if len(slides) >= HERO_SLIDE_LIMIT:
                return slides
    return slides


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
    showcases = FeaturedShowcase.objects.filter(is_active=True).prefetch_related(
        'items__article__images', 'items__article__sizes', 'items__article__category'
    )[:4]
    
    hero_slides = get_hero_slides()
    
    context = {
        'categories': categories,
        'articles': articles,
        'featured_articles': featured_articles,
        'showcases': showcases,
        'selected_category_slug': selected_category_slug,
        'search_query': search_query,
        'hero_slides': hero_slides,
        'hero_images': [s['image_url'] for s in hero_slides],
        'is_homepage': True,
    }
    return render(request, 'store/home.html', context)


def hero_slides_api(request):
    response = JsonResponse({'slides': get_hero_slides()})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response



def article_detail_view(request, slug):
    article = get_object_or_404(
        Article.objects.prefetch_related('images', 'sizes', 'category'),
        slug=slug,
        is_active=True,
    )
    related_articles = Article.objects.filter(
        category=article.category,
        is_active=True,
    ).exclude(id=article.id).prefetch_related('images')[:4]
    
    context = {
        'article': article,
        'related_articles': related_articles,
    }
    return render(request, 'store/product_detail.html', context)


def showcase_detail_view(request, slug):
    if request.user.is_staff:
        showcase = get_object_or_404(
            FeaturedShowcase.objects.prefetch_related(
                'items__article__images',
                'items__article__sizes',
                'items__article__category'
            ),
            slug=slug
        )
    else:
        showcase = get_object_or_404(
            FeaturedShowcase.objects.prefetch_related(
                'items__article__images',
                'items__article__sizes',
                'items__article__category'
            ),
            slug=slug,
            is_active=True
        )

    # Order showcase items by display_order
    ordered_items = showcase.items.filter(
        article__is_active=True
    ).select_related('article__category').prefetch_related(
        'article__images', 'article__sizes'
    ).order_by('display_order', 'id')

    # Other active showcases for recommendation
    other_showcases = FeaturedShowcase.objects.filter(is_active=True).exclude(id=showcase.id)[:3]

    context = {
        'showcase': showcase,
        'ordered_items': ordered_items,
        'other_showcases': other_showcases,
    }
    return render(request, 'store/showcase_detail.html', context)



def get_cart(request):
    return request.session.get('cart', {})


def save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def build_cart_items(request):
    cart = get_cart(request)
    cart_items = []
    total_price = 0
    
    for key, item in cart.items():
        article_id = item.get('article_id')
        size_label = item.get('size')
        color_label = item.get('color', '')
        quantity = item.get('quantity')
        
        try:
            article = Article.objects.get(id=article_id)
            subtotal = article.price * quantity
            total_price += subtotal
            cart_items.append({
                'key': key,
                'article': article,
                'size': size_label,
                'color': color_label,
                'quantity': quantity,
                'subtotal': subtotal,
            })
        except Article.DoesNotExist:
            continue

    return cart_items, total_price


def cart_detail_view(request):
    cart_items, total_price = build_cart_items(request)
            
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'store/cart.html', context)


def cart_contents_api(request):
    cart_items, total_price = build_cart_items(request)
    return JsonResponse({
        'items': [
            {
                'key': item['key'],
                'title': item['article'].title,
                'image': item['article'].primary_image or '',
                'size': item['size'],
                'color': item['color'],
                'quantity': item['quantity'],
                'unit_price': float(item['article'].price),
                'subtotal': float(item['subtotal']),
            }
            for item in cart_items
        ],
        'subtotal': float(total_price),
        'cart_count': sum(item['quantity'] for item in cart_items),
    })


@require_POST
def add_to_cart_api(request):
    try:
        data = json.loads(request.body)
        article_id = data.get('article_id')
        size = data.get('size')
        color = (data.get('color') or '').strip()
        try:
            quantity = int(data.get('quantity', 1))
        except (TypeError, ValueError):
            return JsonResponse({
                'success': False,
                'message': 'Quantity must be a whole number. Color values must be sent in the color field.'
            }, status=400)
        if quantity < 1:
            return JsonResponse({'success': False, 'message': 'Quantity must be at least 1.'}, status=400)
        
        article = get_object_or_404(Article, id=article_id)
        
        # Check variant stock
        if color:
            size_obj = ArticleSize.objects.filter(article=article, size=size, color=color).first()
        else:
            size_obj = ArticleSize.objects.filter(article=article, size=size).first()

        variant_desc = f"size {size}" + (f" and color {color}" if color else "")
        if not size_obj or size_obj.stock_quantity < quantity:
            return JsonResponse({'success': False, 'message': f'Sorry, only {size_obj.stock_quantity if size_obj else 0} left in {variant_desc}.'}, status=400)
            
        cart = get_cart(request)
        cart_key = f"{article_id}_{size}_{color}" if color else f"{article_id}_{size}"
        
        if cart_key in cart:
            cart[cart_key]['quantity'] += quantity
        else:
            cart[cart_key] = {
                'article_id': article.id,
                'title': article.title,
                'price': str(article.price),
                'size': size,
                'color': color,
                'quantity': quantity,
                'image': article.primary_image or '',
            }
            
        save_cart(request, cart)
        total_count = sum(item['quantity'] for item in cart.values())
        return JsonResponse({'success': True, 'cart_count': total_count, 'message': f'Added {article.title} ({variant_desc}) to cart!'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@require_POST
def add_showcase_to_cart_api(request):
    """
    Adds multiple articles selected from a Featured Showcase to the buyer's cart.
    Each selected article is added as its own independent line item (not bundled).
    Respects live Article/ArticleSize stock validation.
    """
    try:
        data = json.loads(request.body)
        items = data.get('items', [])

        if not items:
            return JsonResponse({'success': False, 'message': 'Please select at least one article from the outfit.'}, status=400)

        cart = get_cart(request)
        validated_items = []

        # Step 1: Pre-validate all requested articles, sizes, and optional colors
        for it in items:
            art_id = it.get('article_id')
            size_label = it.get('size')
            color_label = (it.get('color') or '').strip()
            qty = int(it.get('quantity', 1))
            if qty < 1:
                qty = 1

            if not art_id or not size_label:
                return JsonResponse({'success': False, 'message': 'Each selected item must have a chosen size.'}, status=400)

            article = get_object_or_404(Article, id=art_id, is_active=True)
            if color_label:
                size_obj = ArticleSize.objects.filter(article=article, size=size_label, color=color_label).first()
            else:
                size_obj = ArticleSize.objects.filter(article=article, size=size_label).first()

            if not size_obj:
                return JsonResponse({'success': False, 'message': f"Variant '{size_label}' is not available for {article.title}."}, status=400)

            # Check available stock considering what's already in session cart
            cart_key = f"{article.id}_{size_label}_{color_label}" if color_label else f"{article.id}_{size_label}"
            existing_in_cart = cart.get(cart_key, {}).get('quantity', 0)
            if (existing_in_cart + qty) > size_obj.stock_quantity:
                return JsonResponse({
                    'success': False,
                    'message': f"Insufficient stock for {article.title} (Size {size_label}). Available: {size_obj.stock_quantity} (already {existing_in_cart} in your bag)."
                }, status=400)

            validated_items.append((article, size_label, color_label, qty))

        # Step 2: Add each validated article as its own individual line item in the cart
        for article, size_label, color_label, qty in validated_items:
            cart_key = f"{article.id}_{size_label}_{color_label}" if color_label else f"{article.id}_{size_label}"
            if cart_key in cart:
                cart[cart_key]['quantity'] += qty
            else:
                cart[cart_key] = {
                    'article_id': article.id,
                    'title': article.title,
                    'price': str(article.price),
                    'size': size_label,
                    'color': color_label,
                    'quantity': qty,
                    'image': article.primary_image or '',
                }

        save_cart(request, cart)
        total_cart_count = sum(item['quantity'] for item in cart.values())

        # If user is not authenticated, notify client to prompt login/register flow
        require_login = not request.user.is_authenticated
        referer = request.META.get('HTTP_REFERER', '')
        login_url = f"/login/?next={referer or '/checkout/'}"

        return JsonResponse({
            'success': True,
            'cart_count': total_cart_count,
            'added_count': len(validated_items),
            'require_login': require_login,
            'login_url': login_url,
            'message': f"Added {len(validated_items)} outfit piece(s) to your bag!"
        })

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
                col = cart[key].get('color', '')
                if col:
                    size_obj = ArticleSize.objects.filter(article_id=art_id, size=sz, color=col).first()
                else:
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
        color_label = item.get('color', '')
        quantity = item.get('quantity')
        
        try:
            article = Article.objects.get(id=article_id)
            subtotal = article.price * quantity
            total_price += subtotal
            cart_items.append({
                'article': article,
                'size': size_label,
                'color': color_label,
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
                color_label = item.get('color', '').strip()
                quantity = item.get('quantity')
                
                article = Article.objects.select_for_update().get(id=article_id)
                if color_label:
                    size_obj = ArticleSize.objects.select_for_update().filter(article=article, size=size_label, color=color_label).first()
                else:
                    size_obj = ArticleSize.objects.select_for_update().filter(article=article, size=size_label).first()
                
                if not size_obj:
                    variant_desc = f"Size {size_label}" + (f" / Color {color_label}" if color_label else "")
                    raise Exception(f"Variant ({variant_desc}) not found for {article.title}")
                    
                if size_obj.stock_quantity < quantity:
                    variant_desc = f"Size {size_label}" + (f" / Color {color_label}" if color_label else "")
                    raise Exception(f"Insufficient stock for {article.title} ({variant_desc}). Available: {size_obj.stock_quantity}")
                    
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
                    color=color_label,
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
