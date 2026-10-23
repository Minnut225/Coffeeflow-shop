import bcrypt
from django.db import models

class UserRole(models.TextChoices):
    MANAGER = 'MANAGER', 'MANAGER'
    CASHIER = 'CASHIER', 'CASHIER'

class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, db_index=True)
    hashed_password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CASHIER)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def verify_password(self, plain_password: str) -> bool:
        if not self.hashed_password:
            return False
        pwd_bytes = plain_password.encode('utf-8')
        hash_bytes = self.hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(pwd_bytes, hash_bytes)
        except Exception:
            return False

    def set_password(self, plain_password: str):
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

    def __str__(self):
        return f"{self.username} ({self.role})"


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.RESTRICT, db_column='category_id', related_name='products')
    name = models.CharField(max_length=150, db_index=True)
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    price = models.IntegerField()  # Zero-float VND stored as integer
    cost_price = models.IntegerField(default=0)
    image_url = models.TextField(null=True, blank=True)
    is_available = models.BooleanField(default=True, db_index=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Ingredient(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, unique=True, db_index=True)
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    unit = models.CharField(max_length=20)
    stock_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    min_stock_level = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    cost_per_unit = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ingredients'
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} {self.unit})"


class Recipe(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id', related_name='recipes')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.RESTRICT, db_column='ingredient_id', related_name='recipes')
    quantity_required = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        db_table = 'recipes'


class MovementType(models.TextChoices):
    IMPORT = 'IMPORT', 'IMPORT'
    SALE = 'SALE', 'SALE'
    ADJUSTMENT = 'ADJUSTMENT', 'ADJUSTMENT'
    WASTE = 'WASTE', 'WASTE'


class StockMovement(models.Model):
    id = models.AutoField(primary_key=True)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.RESTRICT, db_column='ingredient_id', related_name='stock_movements')
    user = models.ForeignKey(User, on_delete=models.RESTRICT, db_column='user_id', related_name='stock_movements')
    change_amount = models.DecimalField(max_digits=12, decimal_places=3)
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    reference_id = models.CharField(max_length=100, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']


class OrderType(models.TextChoices):
    DINE_IN = 'DINE_IN', 'DINE_IN'
    TAKEAWAY = 'TAKEAWAY', 'TAKEAWAY'


class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'PENDING'
    PAID = 'PAID', 'PAID'
    COMPLETED = 'COMPLETED', 'COMPLETED'
    CANCELLED = 'CANCELLED', 'CANCELLED'


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.RESTRICT, db_column='user_id', related_name='orders')
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    table_number = models.CharField(max_length=20, null=True, blank=True)
    order_type = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.DINE_IN)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True)
    subtotal = models.IntegerField(default=0)  # Zero-float VND
    discount_amount = models.IntegerField(default=0)
    tax_amount = models.IntegerField(default=0)
    total_amount = models.IntegerField(default=0)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id', related_name='items')
    product = models.ForeignKey(Product, on_delete=models.RESTRICT, db_column='product_id', related_name='order_items')
    quantity = models.IntegerField(default=1)
    unit_price = models.IntegerField()  # Price snapshot at order time
    subtotal = models.IntegerField()
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'order_items'


class PaymentMethod(models.TextChoices):
    CASH = 'CASH', 'CASH'
    QR_PAY = 'QR_PAY', 'QR_PAY'
    CARD = 'CARD', 'CARD'


class PaymentStatus(models.TextChoices):
    SUCCESS = 'SUCCESS', 'SUCCESS'
    FAILED = 'FAILED', 'FAILED'
    PENDING = 'PENDING', 'PENDING'


class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.RESTRICT, db_column='order_id', related_name='payments')
    user = models.ForeignKey(User, on_delete=models.RESTRICT, db_column='user_id', related_name='payments')
    amount = models.IntegerField()  # VND integer
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.SUCCESS)
    transaction_code = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']


class AuditAction(models.TextChoices):
    CREATE = 'CREATE', 'CREATE'
    UPDATE = 'UPDATE', 'UPDATE'
    DELETE = 'DELETE', 'DELETE'
    LOGIN = 'LOGIN', 'LOGIN'
    CONFIRM_ORDER = 'CONFIRM_ORDER', 'CONFIRM_ORDER'
    IMPORT_STOCK = 'IMPORT_STOCK', 'IMPORT_STOCK'


class AuditLog(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.RESTRICT, db_column='user_id', null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=AuditAction.choices)
    target_entity = models.CharField(max_length=100)
    target_id = models.CharField(max_length=50, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    ip_address = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
