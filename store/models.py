from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import uuid
import json

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def total_stock(self):
        return sum(size.stock_quantity for size in self.sizes.all())

    @property
    def has_colors(self):
        return any(bool(s.color and s.color.strip()) for s in self.sizes.all())

    @property
    def available_colors(self):
        colors = []
        for s in self.sizes.all():
            if s.color and s.color.strip() and s.color.strip() not in colors:
                colors.append(s.color.strip())
        return colors

    @property
    def available_sizes(self):
        sizes = []
        for s in self.sizes.all():
            if s.size and s.size.strip() not in sizes:
                sizes.append(s.size.strip())
        return sizes

    @property
    def variants_json(self):
        data = [
            {
                'size': (s.size or '').strip(),
                'color': (s.color or '').strip(),
                'stock': s.stock_quantity,
            }
            for s in self.sizes.all()
        ]
        return json.dumps(data)

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        if not img:
            img = self.images.first()
        return img.image.url if img and img.image else None

    @property
    def image_urls(self):
        return json.dumps([
            img.image.url for img in self.images.all() if img.image
        ])

    def __str__(self):
        return f"{self.title} ({self.category.name})"


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='articles/')
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            kwargs.pop('force_update', None)
            kwargs.pop('update_fields', None)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.article.title}"


class ArticleSize(models.Model):
    STANDARD_SIZES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('36', '36'),
        ('37', '37'),
        ('38', '38'),
        ('39', '39'),
        ('40', '40'),
        ('41', '41'),
        ('42', '42'),
        ('43', '43'),
        ('44', '44'),
        ('45', '45'),
        ('One Size', 'One Size'),
    ]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50, blank=True, default='')
    stock_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('article', 'size', 'color')
        ordering = ['size', 'color']

    def __str__(self):
        if self.color:
            return f"{self.article.title} - Size {self.size} / Color {self.color} ({self.stock_quantity} in stock)"
        return f"{self.article.title} - Size {self.size} ({self.stock_quantity} in stock)"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    address = models.TextField()
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.full_name} ({self.user.username})"


class Order(models.Model):
    SOURCE_ONLINE = 'ONLINE'
    SOURCE_IN_STORE = 'IN_STORE'
    SOURCE_CHOICES = [
        (SOURCE_ONLINE, 'Online Order'),
        (SOURCE_IN_STORE, 'In-Store Walk-In'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_SHIPPED = 'SHIPPED'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    client_name = models.CharField(max_length=150)
    client_phone = models.CharField(max_length=30)
    client_address = models.TextField(blank=True)
    client_city = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_ONLINE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"OSH-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} ({self.get_source_display()}) - {self.total_amount} MAD"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    article_title = models.CharField(max_length=200)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50, blank=True, default='')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        if self.color:
            return f"{self.quantity}x {self.article_title} (Size {self.size}, Color {self.color})"
        return f"{self.quantity}x {self.article_title} (Size {self.size})"


class FeaturedShowcase(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='showcases/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Featured Showcase'
        verbose_name_plural = 'Featured Showcases'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while FeaturedShowcase.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def total_outfit_price(self):
        return sum(item.article.price for item in self.items.select_related('article').all() if item.article.is_active)

    @property
    def active_items(self):
        return self.items.filter(article__is_active=True).select_related('article').prefetch_related('article__images', 'article__sizes', 'article__category')

    def __str__(self):
        return self.title


class FeaturedShowcaseItem(models.Model):
    showcase = models.ForeignKey(FeaturedShowcase, on_delete=models.CASCADE, related_name='items')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='showcase_items')
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'id']
        unique_together = ('showcase', 'article')
        verbose_name = 'Showcase Article'
        verbose_name_plural = 'Showcase Articles'

    def __str__(self):
        return f"{self.showcase.title} - #{self.display_order} {self.article.title}"
