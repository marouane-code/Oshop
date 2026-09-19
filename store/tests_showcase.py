from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json

from store.models import Category, Article, ArticleSize, FeaturedShowcase, FeaturedShowcaseItem


class FeaturedShowcaseTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.admin_user = User.objects.create_superuser('admin_user', 'admin@test.com', 'pass123')
        self.buyer_user = User.objects.create_user('buyer_user', 'buyer@test.com', 'pass123')

        # Category
        self.category = Category.objects.create(name='Outerwear')

        # Articles
        self.jacket = Article.objects.create(
            title='Varsity Jacket',
            category=self.category,
            price=600.00,
            is_active=True
        )
        ArticleSize.objects.create(article=self.jacket, size='M', stock_quantity=5)
        ArticleSize.objects.create(article=self.jacket, size='L', stock_quantity=0) # Sold out

        self.tee = Article.objects.create(
            title='Graphic Tee',
            category=self.category,
            price=250.00,
            is_active=True
        )
        ArticleSize.objects.create(article=self.tee, size='M', stock_quantity=10)

        self.pants = Article.objects.create(
            title='Cargo Pants',
            category=self.category,
            price=400.00,
            is_active=True
        )
        ArticleSize.objects.create(article=self.pants, size='32', stock_quantity=4)

        # Showcase
        self.showcase = FeaturedShowcase.objects.create(
            title='Summer Street Look',
            description='Test outfit description',
            is_active=True
        )

        FeaturedShowcaseItem.objects.create(showcase=self.showcase, article=self.jacket, display_order=1)
        FeaturedShowcaseItem.objects.create(showcase=self.showcase, article=self.tee, display_order=2)
        FeaturedShowcaseItem.objects.create(showcase=self.showcase, article=self.pants, display_order=3)

    def test_showcase_model_properties(self):
        """Test slug generation, total outfit price calculation, and item ordering."""
        self.assertEqual(self.showcase.slug, 'summer-street-look')
        self.assertEqual(self.showcase.total_outfit_price, 1250.00) # 600 + 250 + 400
        items = list(self.showcase.items.all())
        self.assertEqual(items[0].article, self.jacket)
        self.assertEqual(items[1].article, self.tee)
        self.assertEqual(items[2].article, self.pants)

    def test_showcase_detail_view_active(self):
        """Active showcase should be viewable by any visitor."""
        url = reverse('store:showcase_detail', kwargs={'slug': self.showcase.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Summer Street Look')
        self.assertContains(response, 'Varsity Jacket')
        self.assertContains(response, 'Graphic Tee')
        self.assertContains(response, 'Cargo Pants')

    def test_showcase_detail_view_inactive(self):
        """Inactive showcase should 404 for normal visitors, but be visible to staff."""
        self.showcase.is_active = False
        self.showcase.save()

        url = reverse('store:showcase_detail', kwargs={'slug': self.showcase.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Staff login
        self.client.force_login(self.admin_user)
        response_staff = self.client.get(url)
        self.assertEqual(response_staff.status_code, 200)

    def test_add_showcase_subset_to_cart_success(self):
        """
        Buyer picks 2 out of 3 articles from the outfit.
        Each should appear as a separate line item in the session cart.
        """
        url = reverse('store:api_cart_add_showcase')
        payload = {
            'items': [
                {'article_id': self.jacket.id, 'size': 'M', 'quantity': 1},
                {'article_id': self.pants.id, 'size': '32', 'quantity': 1}
            ]
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 2)
        self.assertEqual(data['added_count'], 2)
        self.assertTrue(data['require_login']) # Non-authenticated client

        # Check session cart structure
        session_cart = self.client.session.get('cart', {})
        jacket_key = f"{self.jacket.id}_M"
        pants_key = f"{self.pants.id}_32"
        tee_key = f"{self.tee.id}_M"

        self.assertIn(jacket_key, session_cart)
        self.assertIn(pants_key, session_cart)
        self.assertNotIn(tee_key, session_cart) # Tee was NOT selected!

        self.assertEqual(session_cart[jacket_key]['price'], '600.00')
        self.assertEqual(session_cart[pants_key]['price'], '400.00')

    def test_add_showcase_insufficient_stock(self):
        """Should fail if chosen size has 0 or insufficient stock."""
        url = reverse('store:api_cart_add_showcase')
        # Jacket size L is sold out (stock=0)
        payload = {
            'items': [
                {'article_id': self.jacket.id, 'size': 'L', 'quantity': 1}
            ]
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Insufficient stock', data['message'])

    def test_add_showcase_empty_selection(self):
        """Should return 400 if no items are selected."""
        url = reverse('store:api_cart_add_showcase')
        payload = {'items': []}
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_add_showcase_authenticated_user(self):
        """Authenticated user should receive require_login=False."""
        self.client.force_login(self.buyer_user)
        url = reverse('store:api_cart_add_showcase')
        payload = {
            'items': [
                {'article_id': self.tee.id, 'size': 'M', 'quantity': 2}
            ]
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['require_login'])

    def test_admin_toggle_showcase_status_api(self):
        """Admin can toggle showcase status via AJAX API."""
        self.client.force_login(self.admin_user)
        url = reverse('store:admin_showcase_toggle_status', kwargs={'showcase_id': self.showcase.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_active'])

        self.showcase.refresh_from_db()
        self.assertFalse(self.showcase.is_active)


class ColorVariantTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('admin_color', 'admin_color@test.com', 'pass123')
        self.buyer = User.objects.create_user('buyer_color', 'buyer_color@test.com', 'pass123')
        self.category = Category.objects.create(name='Suits')

        # Article with color variants
        self.suit = Article.objects.create(
            title='Italian Wool Suit',
            category=self.category,
            price=1200.00,
            is_active=True
        )
        # Black variants
        ArticleSize.objects.create(article=self.suit, size='M', color='Black', stock_quantity=8)
        ArticleSize.objects.create(article=self.suit, size='L', color='Black', stock_quantity=3)
        # Navy variants
        ArticleSize.objects.create(article=self.suit, size='M', color='Navy', stock_quantity=5)
        ArticleSize.objects.create(article=self.suit, size='L', color='Navy', stock_quantity=0) # Sold out in Navy L

        # Article with NO colors (size-only)
        self.tie = Article.objects.create(
            title='Silk Tie',
            category=self.category,
            price=150.00,
            is_active=True
        )
        ArticleSize.objects.create(article=self.tie, size='One Size', color='', stock_quantity=12)

    def test_article_variant_properties(self):
        """Test has_colors, available_colors, available_sizes, and total_stock."""
        self.assertTrue(self.suit.has_colors)
        self.assertCountEqual(self.suit.available_colors, ['Black', 'Navy'])
        self.assertCountEqual(self.suit.available_sizes, ['M', 'L'])
        self.assertEqual(self.suit.total_stock, 16) # 8 + 3 + 5 + 0

        self.assertFalse(self.tie.has_colors)
        self.assertEqual(self.tie.available_colors, [])
        self.assertEqual(self.tie.available_sizes, ['One Size'])
        self.assertEqual(self.tie.total_stock, 12)

    def test_add_color_variant_to_cart(self):
        """Adding a specific size + color variant to cart."""
        url = reverse('store:api_cart_add')
        payload = {
            'article_id': self.suit.id,
            'size': 'M',
            'color': 'Black',
            'quantity': 2
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 2)

        # Check session cart key
        session_cart = self.client.session.get('cart', {})
        cart_key = f"{self.suit.id}_M_Black"
        self.assertIn(cart_key, session_cart)
        self.assertEqual(session_cart[cart_key]['color'], 'Black')
        self.assertEqual(session_cart[cart_key]['size'], 'M')

    def test_cart_contents_api_matches_session_cart(self):
        """The drawer endpoint exposes the same item and subtotal as checkout."""
        add_url = reverse('store:api_cart_add')
        self.client.post(
            add_url,
            data=json.dumps({
                'article_id': self.suit.id,
                'size': 'M',
                'color': 'Black',
                'quantity': 2,
            }),
            content_type='application/json'
        )

        response = self.client.get(reverse('store:api_cart_contents'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['cart_count'], 2)
        self.assertEqual(data['subtotal'], 2400.0)
        self.assertEqual(data['items'][0]['title'], 'Italian Wool Suit')
        self.assertEqual(data['items'][0]['size'], 'M')
        self.assertEqual(data['items'][0]['color'], 'Black')
        self.assertEqual(data['items'][0]['quantity'], 2)
        self.assertEqual(data['items'][0]['subtotal'], 2400.0)

    def test_add_out_of_stock_color_variant(self):
        """Navy L is sold out (stock=0), should reject addition."""
        url = reverse('store:api_cart_add')
        payload = {
            'article_id': self.suit.id,
            'size': 'L',
            'color': 'Navy',
            'quantity': 1
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('only 0 left', data['message'])

    def test_place_order_decrements_exact_variant_stock(self):
        """Online order should decrement stock for the exact size+color combination."""
        self.client.force_login(self.buyer)

        # Add to cart: 2x Black M (starts at 8), 1x Navy M (starts at 5)
        cart = {
            f"{self.suit.id}_M_Black": {
                'article_id': self.suit.id,
                'title': self.suit.title,
                'price': '1200.00',
                'size': 'M',
                'color': 'Black',
                'quantity': 2
            },
            f"{self.suit.id}_M_Navy": {
                'article_id': self.suit.id,
                'title': self.suit.title,
                'price': '1200.00',
                'size': 'M',
                'color': 'Navy',
                'quantity': 1
            }
        }
        session = self.client.session
        session['cart'] = cart
        session.save()

        # Place order
        url = reverse('store:place_order')
        post_data = {
            'full_name': 'Test Buyer',
            'phone': '0611223344',
            'city': 'Casablanca',
            'address': '123 Boulevard d\'Anfa',
        }
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)

        # Verify stock decrements
        black_m = ArticleSize.objects.get(article=self.suit, size='M', color='Black')
        navy_m = ArticleSize.objects.get(article=self.suit, size='M', color='Navy')
        self.assertEqual(black_m.stock_quantity, 6) # 8 - 2
        self.assertEqual(navy_m.stock_quantity, 4) # 5 - 1

        # Verify OrderItem records color
        from store.models import Order
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 2)

        item1 = order.items.get(color='Black')
        self.assertEqual(item1.size, 'M')
        self.assertEqual(item1.quantity, 2)

        item2 = order.items.get(color='Navy')
        self.assertEqual(item2.size, 'M')
        self.assertEqual(item2.quantity, 1)

    def test_pos_sale_color_variant(self):
        """In-store POS sale decrements exact variant stock and records color."""
        self.client.force_login(self.admin)
        url = reverse('store:admin_pos_process')
        payload = {
            'items': [
                {
                    'article_id': self.suit.id,
                    'size': 'L',
                    'color': 'Black',
                    'quantity': 1
                }
            ],
            'notes': 'In-Store Walk-In Test'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        black_l = ArticleSize.objects.get(article=self.suit, size='L', color='Black')
        self.assertEqual(black_l.stock_quantity, 2) # 3 - 1

