import os
import django
from datetime import timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oshop_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from store.models import Category, Article, ArticleSize, Order, OrderItem, UserProfile

def seed():
    print("🌱 Seeding O-Shop database...")

    # 1. Admin Superuser
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@oshop.ma', 'adminpassword')
        admin.first_name = "Oshop Store Manager"
        admin.save()
        print("✅ Superuser created: admin / adminpassword")
    else:
        admin = User.objects.get(username='admin')

    # 2. Demo Client User
    client_user, created = User.objects.get_or_create(
        username='client@gmail.com',
        defaults={
            'email': 'client@gmail.com',
            'first_name': 'Othmane Alami'
        }
    )
    if created:
        client_user.set_password('clientpassword')
        client_user.save()
        UserProfile.objects.create(
            user=client_user,
            full_name='Othmane Alami',
            phone='0661234567',
            address='Hay Anas, Rue 14, N° 25',
            city='Safi'
        )
        print("✅ Demo Client created: client@gmail.com / clientpassword")

    # 3. Categories
    categories_data = [
        {'name': 'Shoes & Sneakers', 'description': 'Premium urban sneakers and luxury footwear collection.'},
        {'name': 'T-Shirts & Tops', 'description': 'Heavyweight cotton tees and graphic streetwear tops.'},
        {'name': 'Hoodies & Jackets', 'description': 'Oversized fleece hoodies, puffer jackets, and streetwear outerwear.'},
        {'name': 'Pants & Cargo', 'description': 'Tactical cargo pants, relaxed jeans, and urban sweatpants.'},
    ]

    cats = {}
    for cdata in categories_data:
        cat, _ = Category.objects.get_or_create(name=cdata['name'], defaults={'description': cdata['description']})
        cats[cat.name] = cat

    # 4. Articles & Sizes
    articles_data = [
        {
            'title': 'OS Crown Luxury Gold Hoodie',
            'category': cats['Hoodies & Jackets'],
            'price': 499.00,
            'description': 'Heavyweight 450GSM cotton fleece hoodie featuring embroidered gold monogram logo on chest. Oversized drop-shoulder streetwear fit.',
            'is_featured': True,
            'sizes': [('S', 4), ('M', 8), ('L', 12), ('XL', 2)] # Low stock alert on S & XL
        },
        {
            'title': 'O-Shop Urban Black Cargo Pants',
            'category': cats['Pants & Cargo'],
            'price': 389.00,
            'description': 'Multi-pocket tactical cargo trousers in deep obsidian black. Adjustable ankle toggles and gold hardware accents.',
            'is_featured': True,
            'sizes': [('S', 6), ('M', 10), ('L', 5), ('XL', 3)]
        },
        {
            'title': 'O-Shop Monogram High-Top Sneakers',
            'category': cats['Shoes & Sneakers'],
            'price': 699.00,
            'description': 'Handcrafted genuine leather high-top sneakers with gold crown emblem and rubber outsole grip.',
            'is_featured': True,
            'sizes': [('40', 3), ('41', 6), ('42', 7), ('43', 2), ('44', 1)]
        },
        {
            'title': 'Signature O-Shop Oversized Tee (White & Gold)',
            'category': cats['T-Shirts & Tops'],
            'price': 249.00,
            'description': '100% Organic combed cotton 240GSM tee with metallic champagne gold back print.',
            'is_featured': True,
            'sizes': [('S', 10), ('M', 15), ('L', 12), ('XL', 8)]
        },
        {
            'title': 'Safi Streetwear Puffer Jacket',
            'category': cats['Hoodies & Jackets'],
            'price': 799.00,
            'description': 'Insulated thermal puffer jacket with detachable hood and gold-zippered pockets. Perfect for autumn & winter style.',
            'is_featured': False,
            'sizes': [('M', 4), ('L', 6), ('XL', 2)]
        },
        {
            'title': 'Obsidian Retro Runner Sneakers',
            'category': cats['Shoes & Sneakers'],
            'price': 599.00,
            'description': 'Retro-inspired thick sole runners with breathable mesh paneling and reflective gold accents.',
            'is_featured': False,
            'sizes': [('41', 4), ('42', 8), ('43', 5)]
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
            ('Fatima Zohra', '0612345678', 'Safi', 'Hay Anas, Rue 4'),
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
