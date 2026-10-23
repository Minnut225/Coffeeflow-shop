import json
from rest_framework import serializers
from .models import (
    User,
    Category,
    Product,
    Ingredient,
    Recipe,
    Order,
    OrderItem,
    Payment,
    StockMovement,
    AuditLog,
)


class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'role', 'is_active', 'created_at']


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=255)


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'ingredient_id', 'quantity_required']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'display_order', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source='category.id')
    recipes = RecipeSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'category_id',
            'name',
            'sku',
            'price',
            'cost_price',
            'image_url',
            'is_available',
            'description',
            'created_at',
            'updated_at',
            'recipes',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'recipes']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'sku',
            'unit',
            'stock_quantity',
            'min_stock_level',
            'cost_per_unit',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockMovementSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id',
            'ingredient_id',
            'ingredient_name',
            'user_id',
            'change_amount',
            'movement_type',
            'reference_id',
            'note',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'ingredient_name']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product_id',
            'quantity',
            'unit_price',
            'subtotal',
            'note',
            'product_name',
        ]
        read_only_fields = ['id', 'unit_price', 'subtotal', 'product_name']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'amount',
            'payment_method',
            'status',
            'transaction_code',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'user_id',
            'customer_name',
            'table_number',
            'order_type',
            'status',
            'subtotal',
            'discount_amount',
            'tax_amount',
            'total_amount',
            'note',
            'created_at',
            'updated_at',
            'items',
            'payments',
        ]
        read_only_fields = [
            'id',
            'order_number',
            'user_id',
            'subtotal',
            'total_amount',
            'created_at',
            'updated_at',
            'items',
            'payments',
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default=None)
    details = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user_id',
            'username',
            'action',
            'target_entity',
            'target_id',
            'details',
            'ip_address',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'username']

    def get_details(self, obj):
        if not obj.details:
            return None
        try:
            return json.loads(obj.details)
        except Exception:
            return obj.details
