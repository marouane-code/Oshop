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
from store.models import Category, Article, ArticleSize, Order, OrderItem, UserProfile

def seed():
    print("🌱 Seeding Click Shop database...")

    # 1. Admin Superuser
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@clickshop.ma', 'adminpassword')
        admin.first_name = "Click Shop Manager"
        admin.save()
        print("✅ Superuser created: admin / adminpassword")
    else:
        admin = User.objects.get(username='admin')

    # 2. Demo Client User
    client_user, created = User.objects.get_or_create(
        username='client@gmail.com',
        defaults={
            'email': 'client@gmail.com',
            'first_name': 'Hamza Mansouri'
        }
    )
    if created:
        client_user.set_password('clientpassword')
        client_user.save()
        UserProfile.objects.create(
            user=client_user,
            full_name='Hamza Mansouri',
            phone='0661234567',
            address='Sanya, Rue 12, N° 4',
            city='Safi'
        )
        print("✅ Demo Client created: client@gmail.com / clientpassword")

    # 3. Categories
    categories_data = [
        {'name': 'Shoes & Sneakers', 'description': 'Curated urban footwear and minimalist low-profile sneakers.'},
        {'name': 'T-Shirts & Tops', 'description': 'Heavyweight combed cotton tees and modern graphic streetwear.'},
        {'name': 'Hoodies & Jackets', 'description': 'Oversized luxury fleece hoodies, puffers, and minimal outerwear.'},
        {'name': 'Pants & Cargo', 'description': 'Tailored cargo trousers, relaxed denim, and modern streetwear pants.'},
    ]

    cats = {}
    for cdata in categories_data:
        cat, _ = Category.objects.get_or_create(name=cdata['name'], defaults={'description': cdata['description']})
        cats[cat.name] = cat

    # 4. Articles & Sizes
    articles_data = [
        {
            'title': 'Click Shop Heavyweight Monochrome Hoodie',
            'category': cats['Hoodies & Jackets'],
            'price': 449.00,
            'description': '460GSM ultra-dense organic cotton fleece hoodie in clean jet black. Subtle tonal chest embroidery with modern boxy drop-shoulder silhouette.',
            'is_featured': True,
            'sizes': [('S', 5), ('M', 10), ('L', 12), ('XL', 4)]
        },
        {
            'title': 'Click Shop Minimalist Cargo Trousers',
            'category': cats['Pants & Cargo'],
            'price': 389.00,
            'description': 'Clean-cut utilitarian cargo trousers in matte black. Concealed snap pockets and adjustable bungee hems for versatile styling.',
            'is_featured': True,
            'sizes': [('S', 6), ('M', 12), ('L', 8), ('XL', 3)]
        },
        {
            'title': 'Click Shop Low-Profile Urban Sneakers',
            'category': cats['Shoes & Sneakers'],
            'price': 649.00,
            'description': 'Clean monochrome leather low-top sneakers with cushioned cupsole and debossed branding. Hand-stitched detailing.',
            'is_featured': True,
            'sizes': [('40', 4), ('41', 8), ('42', 10), ('43', 6), ('44', 3)]
        },
        {
            'title': 'Click Shop Essential Heavyweight Tee',
            'category': cats['T-Shirts & Tops'],
            'price': 229.00,
            'description': '260GSM combed organic cotton tee in crisp optic white. Ribbed mock collar and structured relaxed fit.',
            'is_featured': True,
            'sizes': [('S', 12), ('M', 20), ('L', 18), ('XL', 8)]
        },
        {
            'title': 'Click Shop Sanya Insulated Puffer Jacket',
            'category': cats['Hoodies & Jackets'],
            'price': 749.00,
            'description': 'Water-repellent matte-finish puffer jacket with lightweight thermal insulation, high-stand collar, and matte hardware.',
            'is_featured': False,
            'sizes': [('M', 5), ('L', 8), ('XL', 3)]
        },
        {
            'title': 'Click Shop Contrast Sole Runner',
            'category': cats['Shoes & Sneakers'],
            'price': 579.00,
            'description': 'Contemporary aerodynamic runners featuring technical mesh and premium suede accents in black and off-white.',
            'is_featured': False,
            'sizes': [('41', 5), ('42', 7), ('43', 6)]
        }
    ]

    for adata in articles_data:
        sizes_spec = adata.pop('sizes')
        art, created = Article.objects.get_or_create(title=adata['title'], defaults=adata)
        if created:
            for sz, qty in sizes_spec:
                ArticleSize.objects.create(article=art, size=sz, stock_quantity=qty)

    print("✅ Sample Articles & Sizes populated.")

    # 5. Orders Seed (Online & Walk-In Sales)
    now = timezone.now()
    if Order.objects.count() == 0:
        sample_articles = Article.objects.all()
        buyers = [
            ('Youssef Benani', '0665432109', 'Casablanca', 'Bd Zerktouni, Res Al Amal'),
            ('Khadija El Mansouri', '0671122334', 'Rabat', 'Agdal, Rue Omar Ibn Khattab'),
            ('Amine Chraibi', '0659988776', 'Marrakech', 'Gueliz, Ave Mohammed V'),
            ('Fatima Zohra', '0612345678', 'Safi', 'Sanya, Rue 4'),
            ('Walk-In Customer', 'N/A', 'Safi', 'In-Store Walk-In Sale')
        ]

        for i in range(12):
            days_ago = random.randint(0, 10)
            order_date = now - timedelta(days=days_ago, hours=random.randint(1, 10))
            source = Order.SOURCE_IN_STORE if i % 3 == 0 else Order.SOURCE_ONLINE
            status = Order.STATUS_DELIVERED if (days_ago > 2 or source == Order.SOURCE_IN_STORE) else random.choice([Order.STATUS_PENDING, Order.STATUS_CONFIRMED, Order.STATUS_SHIPPED])
            
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
            # Override auto_now_add for historical chart
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
