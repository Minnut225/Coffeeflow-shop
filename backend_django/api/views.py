import json
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import (
    User,
    UserRole,
    Category,
    Product,
    Ingredient,
    Recipe,
    Order,
    OrderItem,
    OrderStatus,
    OrderType,
    Payment,
    PaymentMethod,
    PaymentStatus,
    StockMovement,
    MovementType,
    AuditLog,
    AuditAction,
)
from .serializers import (
    UserResponseSerializer,
    LoginRequestSerializer,
    CategorySerializer,
    ProductSerializer,
    IngredientSerializer,
    StockMovementSerializer,
    OrderSerializer,
    OrderItemSerializer,
    PaymentSerializer,
    AuditLogSerializer,
)
from .authentication import (
    create_access_token,
    IsManager,
    IsCashierOrManager,
)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# =========================================================================
# AUTHENTICATION VIEWS
# =========================================================================

class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"detail": "Incorrect username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.verify_password(password):
            return Response(
                {"detail": "Incorrect username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"detail": "User account is disabled"},
                status=status.HTTP_403_FORBIDDEN
            )

        access_token = create_access_token(data={"sub": user.username, "role": user.role})

        # Record login audit
        AuditLog.objects.create(
            user=user,
            action=AuditAction.LOGIN,
            target_entity="USER",
            target_id=str(user.id),
            details=f"User {user.username} logged in",
            ip_address=get_client_ip(request),
        )

        return Response({
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role,
            "full_name": user.full_name,
        })


class CurrentUserView(APIView):
    permission_classes = [IsCashierOrManager]

    def get(self, request):
        serializer = UserResponseSerializer(request.user)
        return Response(serializer.data)


# =========================================================================
# CATEGORIES VIEWS
# =========================================================================

class CategoryListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsCashierOrManager()]
        return [IsManager()]

    def get(self, request):
        categories = Category.objects.all().order_by('display_order', 'id')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        category = serializer.save()
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsCashierOrManager()]
        return [IsManager()]

    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"detail": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(CategorySerializer(category).data)

    def put(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"detail": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"detail": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================================================================
# PRODUCTS VIEWS
# =========================================================================

class ProductListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsCashierOrManager()]
        return [IsManager()]

    def get(self, request):
        queryset = Product.objects.select_related('category').prefetch_related('recipes').all()
        category_id = request.query_params.get('category_id')
        is_active = request.query_params.get('is_active')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if is_active is not None:
            active_bool = is_active.lower() in ('true', '1')
            queryset = queryset.filter(is_available=active_bool)

        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        category_id = data.get('category_id')
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({"detail": f"Category with id {category_id} not found"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            product = Product.objects.create(
                category=category,
                name=data.get('name'),
                sku=data.get('sku'),
                price=int(data.get('price', 0)),
                cost_price=int(data.get('cost_price', 0)),
                image_url=data.get('image_url', ''),
                is_available=data.get('is_available', True),
                description=data.get('description', ''),
            )

            recipes_data = data.get('recipes', [])
            for r in recipes_data:
                ing_id = r.get('ingredient_id')
                qty = r.get('quantity_required')
                if ing_id and qty:
                    Recipe.objects.create(
                        product=product,
                        ingredient_id=ing_id,
                        quantity_required=Decimal(str(qty)),
                    )

        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsCashierOrManager()]
        return [IsManager()]

    def get_object(self, pk):
        try:
            return Product.objects.select_related('category').prefetch_related('recipes').get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)

    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        with transaction.atomic():
            if 'category_id' in data:
                try:
                    product.category = Category.objects.get(id=data['category_id'])
                except Category.DoesNotExist:
                    return Response({"detail": "Category not found"}, status=status.HTTP_400_BAD_REQUEST)

            for field in ['name', 'sku', 'price', 'cost_price', 'image_url', 'is_available', 'description']:
                if field in data:
                    setattr(product, field, data[field])
            product.save()

            if 'recipes' in data and isinstance(data['recipes'], list):
                product.recipes.all().delete()
                for r in data['recipes']:
                    Recipe.objects.create(
                        product=product,
                        ingredient_id=r['ingredient_id'],
                        quantity_required=Decimal(str(r['quantity_required'])),
                    )

        product.refresh_from_db()
        return Response(ProductSerializer(product).data)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================================================================
# INVENTORY & INGREDIENT VIEWS
# =========================================================================

class IngredientListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsCashierOrManager()]
        return [IsManager()]

    def get(self, request):
        ingredients = Ingredient.objects.all().order_by('id')
        serializer = IngredientSerializer(ingredients, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = IngredientSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        ingredient = serializer.save()
        return Response(IngredientSerializer(ingredient).data, status=status.HTTP_201_CREATED)


class IngredientDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsCashierOrManager()]
        return [IsManager()]

    def get_object(self, pk):
        try:
            return Ingredient.objects.get(pk=pk)
        except Ingredient.DoesNotExist:
            return None

    def get(self, request, pk):
        ingredient = self.get_object(pk)
        if not ingredient:
            return Response({"detail": "Ingredient not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(IngredientSerializer(ingredient).data)

    def put(self, request, pk):
        ingredient = self.get_object(pk)
        if not ingredient:
            return Response({"detail": "Ingredient not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = IngredientSerializer(ingredient, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


class StockImportView(APIView):
    permission_classes = [IsManager]

    def post(self, request):
        data = request.data
        items = data.get('items', [])
        general_note = data.get('note', '')

        # Single item fallback format: { ingredient_id, quantity, note }
        if not items and 'ingredient_id' in data:
            items = [{
                'ingredient_id': data.get('ingredient_id'),
                'quantity': data.get('quantity'),
                'cost_per_unit': data.get('cost_per_unit'),
                'note': data.get('note', ''),
            }]

        if not items:
            return Response({"detail": "No items provided for stock import"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for item in items:
                ing_id = item.get('ingredient_id')
                qty = Decimal(str(item.get('quantity', 0)))
                cost = item.get('cost_per_unit')
                note = item.get('note') or general_note

                if qty <= 0:
                    return Response({"detail": "Quantity must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    ingredient = Ingredient.objects.select_for_update().get(id=ing_id)
                except Ingredient.DoesNotExist:
                    return Response({"detail": f"Ingredient {ing_id} not found"}, status=status.HTTP_404_NOT_FOUND)

                ingredient.stock_quantity += qty
                if cost is not None:
                    ingredient.cost_per_unit = int(cost)
                ingredient.save()

                StockMovement.objects.create(
                    ingredient=ingredient,
                    user=request.user,
                    change_amount=qty,
                    movement_type=MovementType.IMPORT,
                    note=note,
                )

                AuditLog.objects.create(
                    user=request.user,
                    action=AuditAction.IMPORT_STOCK,
                    target_entity="INGREDIENT",
                    target_id=str(ingredient.id),
                    details=f"Imported {qty} {ingredient.unit} of {ingredient.name}",
                    ip_address=get_client_ip(request),
                )

        return Response({"message": "Import stock successful"}, status=status.HTTP_200_OK)


class StockMovementListView(APIView):
    permission_classes = [IsCashierOrManager]

    def get(self, request):
        movements = StockMovement.objects.select_related('ingredient', 'user').all().order_by('-created_at')[:100]
        serializer = StockMovementSerializer(movements, many=True)
        return Response(serializer.data)


# =========================================================================
# ORDERS & POS VIEWS
# =========================================================================

class OrderListCreateView(APIView):
    permission_classes = [IsCashierOrManager]

    def get(self, request):
        queryset = Order.objects.prefetch_related('items__product', 'payments').all().order_by('-created_at')
        status_filter = request.query_params.get('status')
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))

        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        orders = queryset[offset:offset + limit]
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        items_data = data.get('items', [])
        if not items_data:
            return Response({"detail": "Order must contain at least one item"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            now_str = timezone.now().strftime("%Y%m%d%H%M%S")
            unique_suffix = uuid.uuid4().hex[:6].upper()
            order_number = f"ORD-{now_str}-{unique_suffix}"

            discount_amount = int(data.get('discount_amount', 0))
            tax_amount = int(data.get('tax_amount', 0))

            order = Order.objects.create(
                order_number=order_number,
                user=request.user,
                customer_name=data.get('customer_name') or None,
                table_number=str(data.get('table_number')) if data.get('table_number') is not None else None,
                order_type=data.get('order_type', OrderType.DINE_IN),
                status=OrderStatus.PENDING,
                discount_amount=discount_amount,
                tax_amount=tax_amount,
                subtotal=0,
                total_amount=0,
                note=data.get('note') or None,
            )

            subtotal = 0
            order_items = []

            for item in items_data:
                product_id = item.get('product_id')
                quantity = int(item.get('quantity', 1))
                item_note = item.get('note') or item.get('notes')

                if quantity <= 0:
                    return Response({"detail": "Item quantity must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    return Response({"detail": f"Product {product_id} not found"}, status=status.HTTP_404_NOT_FOUND)

                if not product.is_available:
                    return Response({"detail": f"Product '{product.name}' is currently unavailable"}, status=status.HTTP_400_BAD_REQUEST)

                unit_price = product.price
                item_subtotal = unit_price * quantity
                subtotal += item_subtotal

                order_items.append(OrderItem(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=item_subtotal,
                    note=item_note or None,
                ))

            OrderItem.objects.bulk_create(order_items)

            total_amount = max(0, subtotal - discount_amount + tax_amount)
            order.subtotal = subtotal
            order.total_amount = total_amount
            order.save()

            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.CREATE,
                target_entity="ORDER",
                target_id=str(order.id),
                details=f"Created order {order.order_number} with total {total_amount} VND",
                ip_address=get_client_ip(request),
            )

        order.refresh_from_db()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsCashierOrManager]

    def get_object(self, pk):
        try:
            return Order.objects.prefetch_related('items__product', 'payments').get(pk=pk)
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        order = self.get_object(pk)
        if not order:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


class OrderCheckoutView(APIView):
    permission_classes = [IsCashierOrManager]

    def post(self, request, pk):
        try:
            order = Order.objects.prefetch_related('items__product__recipes__ingredient').get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            return Response({"detail": f"Cannot checkout order in status {order.status}"}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        payment_method = data.get('payment_method', PaymentMethod.CASH)
        amount_paid = int(data.get('amount_paid', order.total_amount))
        transaction_code = data.get('transaction_code') or f"TXN-{order.order_number}"

        if amount_paid < order.total_amount:
            return Response({"detail": "Amount paid is less than order total"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Concurrency-safe stock deduction via recipes
            ingredient_deductions = {}
            for item in order.items.all():
                for recipe in item.product.recipes.all():
                    needed = recipe.quantity_required * item.quantity
                    ingredient_deductions[recipe.ingredient_id] = ingredient_deductions.get(recipe.ingredient_id, Decimal(0)) + needed

            # Lock ingredients and deduct
            for ing_id, deduct_qty in ingredient_deductions.items():
                try:
                    ingredient = Ingredient.objects.select_for_update().get(id=ing_id)
                except Ingredient.DoesNotExist:
                    continue

                if ingredient.stock_quantity < deduct_qty:
                    return Response({
                        "detail": f"Insufficient stock for ingredient '{ingredient.name}'. Available: {ingredient.stock_quantity}, Required: {deduct_qty}"
                    }, status=status.HTTP_400_BAD_REQUEST)

                ingredient.stock_quantity -= deduct_qty
                ingredient.save()

                StockMovement.objects.create(
                    ingredient=ingredient,
                    user=request.user,
                    change_amount=-deduct_qty,
                    movement_type=MovementType.SALE,
                    reference_id=str(order.id),
                    note=f"Sale for order {order.order_number}",
                )

            # Record Payment
            payment = Payment.objects.create(
                order=order,
                user=request.user,
                amount=order.total_amount,
                payment_method=payment_method,
                status=PaymentStatus.SUCCESS,
                transaction_code=transaction_code,
            )

            # Complete Order
            order.status = OrderStatus.COMPLETED
            order.save()

            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.CONFIRM_ORDER,
                target_entity="ORDER",
                target_id=str(order.id),
                details=f"Checked out order {order.order_number} for {order.total_amount} VND via {payment_method}",
                ip_address=get_client_ip(request),
            )

        change_due = max(0, amount_paid - order.total_amount)
        return Response({
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": order.total_amount,
            "amount_paid": amount_paid,
            "change_due": change_due,
            "payment": PaymentSerializer(payment).data,
            "message": "Payment successful and order completed",
        }, status=status.HTTP_200_OK)


class OrderConfirmView(APIView):
    permission_classes = [IsCashierOrManager]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.PAID
            order.save()

        return Response(OrderSerializer(order).data)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsCashierOrManager]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if not new_status:
            return Response({"detail": "Status field is required"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status.upper()
        if order.status == OrderStatus.PAID and not order.payments.exists():
            Payment.objects.create(
                order=order,
                user=request.user,
                amount=order.total_amount,
                payment_method=PaymentMethod.CASH,
                status=PaymentStatus.SUCCESS,
                transaction_code=f"TXN-{order.order_number}",
            )
        order.save()

        return Response(OrderSerializer(order).data)


# =========================================================================
# MANAGEMENT DASHBOARD & REPORTS VIEWS
# =========================================================================

class DashboardMetricsView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        completed_orders = Order.objects.filter(status=OrderStatus.COMPLETED).prefetch_related('items')
        total_revenue = sum(o.total_amount for o in completed_orders)
        total_orders = completed_orders.count()
        total_items_sold = sum(item.quantity for o in completed_orders for item in o.items.all())

        active_tables_count = Order.objects.filter(
            status__in=[OrderStatus.PENDING, OrderStatus.PAID],
            table_number__isnull=False
        ).values('table_number').distinct().count()

        pending_orders = Order.objects.filter(status__in=[OrderStatus.PENDING, OrderStatus.PAID]).count()
        low_stock_count = Ingredient.objects.filter(stock_quantity__lte=F('min_stock_level')).count()

        return Response({
            "total_revenue": int(total_revenue),
            "total_orders": total_orders,
            "total_items_sold": total_items_sold,
            "active_tables": active_tables_count,
            "pending_orders": pending_orders,
            "low_stock_count": low_stock_count,
            "revenue_growth_percent": 5.4,
        })


class SalesReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by = request.query_params.get('group_by', 'day')
        period = request.query_params.get('period')

        if period:
            today = timezone.now().date()
            if period == 'today':
                start_date = today.isoformat()
                end_date = today.isoformat()
                group_by = 'day'
            elif period == 'week':
                start_date = (today - timedelta(days=7)).isoformat()
                end_date = today.isoformat()
                group_by = 'day'
            elif period == 'month':
                start_date = (today - timedelta(days=30)).isoformat()
                end_date = today.isoformat()
                group_by = 'day'

        queryset = Order.objects.filter(status=OrderStatus.COMPLETED).prefetch_related('items')

        if start_date:
            try:
                dt_start = datetime.fromisoformat(start_date)
                if timezone.is_naive(dt_start):
                    dt_start = timezone.make_aware(dt_start)
                queryset = queryset.filter(created_at__gte=dt_start)
            except ValueError:
                pass

        if end_date:
            try:
                dt_end = datetime.fromisoformat(end_date)
                if timezone.is_naive(dt_end):
                    dt_end = timezone.make_aware(dt_end)
                queryset = queryset.filter(created_at__lte=dt_end)
            except ValueError:
                pass

        grouped_data = {}
        total_revenue = 0
        total_items_sold = 0
        orders = list(queryset)

        for o in orders:
            if o.created_at:
                if group_by == 'month':
                    key = o.created_at.strftime('%Y-%m')
                elif group_by == 'week':
                    year, week, _ = o.created_at.isocalendar()
                    key = f"{year}-W{week:02d}"
                else:
                    key = o.created_at.strftime('%Y-%m-%d')
            else:
                key = 'unknown'

            if key not in grouped_data:
                grouped_data[key] = {
                    "period": key,
                    "order_count": 0,
                    "revenue": 0,
                    "items_sold": 0,
                    "gross_sales": 0,
                    "net_sales": 0,
                    "discounts": 0,
                }

            items_count = sum(item.quantity for item in o.items.all())
            grouped_data[key]["order_count"] += 1
            grouped_data[key]["revenue"] += o.total_amount
            grouped_data[key]["gross_sales"] += o.total_amount
            grouped_data[key]["net_sales"] += o.total_amount
            grouped_data[key]["items_sold"] += items_count

            total_revenue += o.total_amount
            total_items_sold += items_count

        items = sorted(grouped_data.values(), key=lambda x: x["period"])
        total_orders = len(orders)
        avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0.0

        return Response({
            "items": items,
            "summary": {
                "total_revenue": total_revenue,
                "total_gross_sales": total_revenue,
                "total_net_sales": total_revenue,
                "total_orders": total_orders,
                "total_items_sold": total_items_sold,
                "average_order_value": avg_order_value,
            },
            "group_by": group_by,
        })


class AuditLogListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsManager()]
        return [IsCashierOrManager()]

    def get(self, request):
        queryset = AuditLog.objects.select_related('user').all().order_by('-created_at')
        user_id = request.query_params.get('user_id')
        action = request.query_params.get('action')
        target_entity = request.query_params.get('target_entity')
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)
        if target_entity:
            queryset = queryset.filter(target_entity=target_entity)

        total = queryset.count()
        logs = queryset[offset:offset + limit]
        serializer = AuditLogSerializer(logs, many=True)

        return Response({
            "total": total,
            "items": serializer.data,
            "page": (offset // limit) + 1 if limit else 1,
            "size": limit,
        })

    def post(self, request):
        data = request.data
        details = data.get('details')
        if isinstance(details, dict):
            details = json.dumps(details)

        log = AuditLog.objects.create(
            user=request.user,
            action=data.get('action', AuditAction.CREATE),
            target_entity=data.get('target_entity', ''),
            target_id=str(data.get('target_id', '')) if data.get('target_id') else None,
            details=details,
            ip_address=get_client_ip(request),
        )
        return Response(AuditLogSerializer(log).data, status=status.HTTP_201_CREATED)


class EmployeeListView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        users = User.objects.all().order_by('id')
        serializer = UserResponseSerializer(users, many=True)
        return Response(serializer.data)


class InventoryStatusView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        ingredients = Ingredient.objects.all().order_by('id')
        items = [
            {
                "id": ing.id,
                "name": ing.name,
                "unit": ing.unit,
                "stock_quantity": int(ing.stock_quantity),
                "min_stock_threshold": int(ing.min_stock_level),
                "cost_per_unit": ing.cost_per_unit,
                "updated_at": ing.updated_at.isoformat() if ing.updated_at else None,
            }
            for ing in ingredients
        ]
        return Response(items)


class ReportsSummaryView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        completed = Order.objects.filter(status=OrderStatus.COMPLETED)
        total_rev = sum(o.total_amount for o in completed)
        return Response({
            "total_revenue": total_rev,
            "total_orders": completed.count(),
            "status": "success",
        })
