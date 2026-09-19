import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import django
from datetime import timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clickshop_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from store.models import Category, Article, ArticleImage, ArticleSize, Order, OrderItem, UserProfile, FeaturedShowcase, FeaturedShowcaseItem

def seed():
    print("🌱 Seeding Mario Clothes database (marioclothes_db)...")

    # 1. Admin Superuser
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@marioclothes.ma', 'adminpassword')
        admin.first_name = "Mario Clothes Manager"
        admin.save()
        print("✅ Superuser created: admin / adminpassword")
    else:
        admin = User.objects.get(username='admin')
        admin.first_name = "Mario Clothes Manager"
        admin.email = 'admin@marioclothes.ma'
        admin.save()

    # 2. Demo Client User
    client_user, created = User.objects.get_or_create(
        username='client@gmail.com',
        defaults={
            'email': 'client@gmail.com',
            'first_name': 'Mehdi Benjelloun'
        }
    )
    if created:
        client_user.set_password('clientpassword')
        client_user.save()
        UserProfile.objects.create(
            user=client_user,
            full_name='Mehdi Benjelloun',
            phone='0772379035',
            address='Casablanca city center, Bab Marrakech',
            city='Casablanca'
        )
        print("✅ Demo Client created: client@gmail.com / clientpassword")

    # 3. High-End Men's Fashion Categories
    categories_data = [
        {'name': 'Costumes & Blazers', 'description': 'Costumes sur-mesure, blazers élégants et coupes sartoriales italiennes.'},
        {'name': 'Chemises & Polos', 'description': 'Chemises en coton d\'Égypte, popeline stretch et polos en maille texturée.'},
        {'name': 'Pantalons & Chinos', 'description': 'Pantalons à pinces, chinos ajustés et finitions haut de gamme.'},
        {'name': 'Vestes & Manteaux', 'description': 'Manteaux en laine, blousons raffinés et pardessus intemporels.'},
        {'name': 'Chaussures & Mocassins', 'description': 'Mocassins en cuir véritable, souliers italiens et baskets chic.'},
    ]

    cats = {}
    for cdata in categories_data:
        cat, _ = Category.objects.get_or_create(name=cdata['name'], defaults={'description': cdata['description']})
        cats[cat.name] = cat

    # Available article photos in media/articles
    media_dir = os.path.join(os.path.dirname(__file__), 'media', 'articles')
    available_images = []
    if os.path.exists(media_dir):
        available_images = [f"articles/{f}" for f in os.listdir(media_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

    # 4. Articles & Sizes
    articles_data = [
        {
            'title': 'Costume Mario Sartoriale Slim Fit',
            'category': cats['Costumes & Blazers'],
            'price': 1490.00,
            'description': 'Costume deux pièces confectionné dans un tissu haut de gamme avec revers cranté, coupe cintrée et finitions sartoriales italiennes.',
            'is_featured': True,
            'sizes': [('48', 4), ('50', 8), ('52', 6), ('54', 3)]
        },
        {
            'title': 'Blazer Milano en Laine Texturée',
            'category': cats['Costumes & Blazers'],
            'price': 990.00,
            'description': 'Blazer élégant non doublé pour un confort optimal, poches plaquées et boutons en corne naturelle.',
            'is_featured': True,
            'sizes': [('M', 5), ('L', 7), ('XL', 4)]
        },
        {
            'title': 'Chemise Blanche Coton Supima Slim',
            'category': cats['Chemises & Polos'],
            'price': 390.00,
            'description': 'Chemise habillée en popeline de coton d\'Égypte douce et respirante, col français et poignets biseautés.',
            'is_featured': True,
            'sizes': [('M', 10), ('L', 15), ('XL', 12), ('XXL', 5)]
        },
        {
            'title': 'Polo Maille Piquée Prestige',
            'category': cats['Chemises & Polos'],
            'price': 320.00,
            'description': 'Polo en maille de coton mercerisé, col chemise structuré et patte de boutonnage discrète.',
            'is_featured': True,
            'sizes': [('S', 4), ('M', 12), ('L', 10), ('XL', 6)]
        },
        {
            'title': 'Pantalon Chino Sartorial à Pinces',
            'category': cats['Pantalons & Chinos'],
            'price': 480.00,
            'description': 'Pantalon habillé à pli frontal et pattes de serrage latérales, tombé parfait et élégance moderne.',
            'is_featured': True,
            'sizes': [('38', 5), ('40', 8), ('42', 10), ('44', 6)]
        },
        {
            'title': 'Mocassins Cuir Suédé Mario Handcrafted',
            'category': cats['Chaussures & Mocassins'],
            'price': 790.00,
            'description': 'Mocassins à pampilles en veau velours italien, semelle cousue Blake et intérieur cuir ultra-confort.',
            'is_featured': True,
            'sizes': [('40', 4), ('41', 8), ('42', 12), ('43', 9), ('44', 5)]
        },
        {
            'title': 'Manteau Pardessus en Laine Noir Intense',
            'category': cats['Vestes & Manteaux'],
            'price': 1250.00,
            'description': 'Pardessus droit mi-long en drap de laine mélangée, fente d\'aisance au dos et poches à rabat passepoilées.',
            'is_featured': True,
            'sizes': [('M', 3), ('L', 6), ('XL', 5)]
        },
        {
            'title': 'Veste Bombardier en Suédine Douce',
            'category': cats['Vestes & Manteaux'],
            'price': 850.00,
            'description': 'Veste casual chic en suédine toucher velours, finitions bords-côtes et zip métallique haut de gamme.',
            'is_featured': False,
            'sizes': [('M', 5), ('L', 8), ('XL', 4)]
        }
    ]

    for idx, adata in enumerate(articles_data):
        sizes_spec = adata.pop('sizes')
        art, created = Article.objects.get_or_create(title=adata['title'], defaults=adata)
        if created:
            for sz, qty in sizes_spec:
                ArticleSize.objects.create(article=art, size=sz, stock_quantity=qty)
            
            # Attach an image if available
            if available_images:
                img_path = available_images[idx % len(available_images)]
                ArticleImage.objects.create(article=art, image=img_path, is_primary=True)

    print("✅ High-End Men's Articles & Sizes populated.")

    # 5. Featured Showcase
    if Article.objects.exists() and FeaturedShowcase.objects.count() == 0:
        showcase = FeaturedShowcase.objects.create(
            title="L'Allure Sartoriale Mario Clothes",
            description="L'ensemble complet parfait pour vos rendez-vous d'affaires et soirées distinguées.",
            is_active=True
        )
        sample_arts = list(Article.objects.filter(is_active=True)[:3])
        for s_idx, a_item in enumerate(sample_arts):
            FeaturedShowcaseItem.objects.create(
                showcase=showcase,
                article=a_item,
                display_order=s_idx
            )
        print("✅ Featured Showcase created.")

    # 6. Orders Seed (Online & In-Store Sales)
    now = timezone.now()
    if Order.objects.count() == 0:
        sample_articles = Article.objects.all()
        buyers = [
            ('Mehdi Benjelloun', '0772379035', 'Casablanca', 'Bab Marrakech, Centre-ville'),
            ('Tarik Berrada', '0661122334', 'Rabat', 'Agdal, Ave Fal Ould Oumeir'),
            ('Reda Kabbaj', '0665987654', 'Casablanca', 'Gauthier, Rue Jean Jaurès'),
            ('Othmane Sebti', '0662334455', 'Marrakech', 'Hivernage, Ave Mohammed VI'),
            ('Client Boutique (Walk-In)', 'N/A', 'Casablanca', 'Vente Directe Boutique Bab Marrakech')
        ]

        for i in range(10):
            days_ago = random.randint(0, 7)
            order_date = now - timedelta(days=days_ago, hours=random.randint(1, 10))
            source = Order.SOURCE_IN_STORE if i % 3 == 0 else Order.SOURCE_ONLINE
            status = Order.STATUS_DELIVERED if (days_ago > 1 or source == Order.SOURCE_IN_STORE) else random.choice([Order.STATUS_PENDING, Order.STATUS_CONFIRMED, Order.STATUS_SHIPPED])
            
            buyer = random.choice(buyers)
            
            ord_obj = Order.objects.create(
                user=client_user if source == Order.SOURCE_ONLINE else admin,
                client_name=buyer[0],
                client_phone=buyer[1],
                client_city=buyer[2],
                client_address=buyer[3],
                source=source,
                status=status,
                created_at=order_date
            )
            Order.objects.filter(id=ord_obj.id).update(created_at=order_date)

            art = random.choice(sample_articles)
            sz = art.sizes.first()
            qty = random.randint(1, 2)
            subtotal = art.price * qty

            OrderItem.objects.create(
                order=ord_obj,
                article=art,
                article_title=art.title,
                size=sz.size if sz else 'M',
                quantity=qty,
                unit_price=art.price,
                subtotal=subtotal
            )

            ord_obj.total_amount = subtotal
            ord_obj.save()

        print("✅ Sample Orders & POS sales seeded.")

if __name__ == '__main__':
    seed()
