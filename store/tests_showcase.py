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
