from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    User,
    UserRole,
    Category,
    Product,
    Ingredient,
    Recipe,
    Order,
    OrderStatus,
    OrderType,
)


class CoffeeFlowDjangoAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Manager
        self.manager = User(
            username="test_manager",
            full_name="Manager Test",
            role=UserRole.MANAGER,
            is_active=True,
        )
        self.manager.set_password("password123")
        self.manager.save()

        # Create Cashier
        self.cashier = User(
            username="test_cashier",
            full_name="Cashier Test",
            role=UserRole.CASHIER,
            is_active=True,
        )
        self.cashier.set_password("password123")
        self.cashier.save()

        # Create Category
        self.category = Category.objects.create(
            name="Cà phê pha phin",
            display_order=1,
            is_active=True,
        )

        # Create Ingredient
        self.ingredient = Ingredient.objects.create(
            name="Hạt Robusta Test",
            sku="ING-ROB-TEST",
            unit="g",
            stock_quantity=Decimal("5000.0"),
            min_stock_level=Decimal("500.0"),
            cost_per_unit=200,
        )

        # Create Product
        self.product = Product.objects.create(
            category=self.category,
            name="Cà phê đen Test",
            sku="CF-DEN-TEST",
            price=25000,
            cost_price=5000,
            is_available=True,
        )

        # Create Recipe
        self.recipe = Recipe.objects.create(
            product=self.product,
            ingredient=self.ingredient,
            quantity_required=Decimal("20.0"),
        )

    def login_user(self, username="test_manager", password="password123"):
        res = self.client.post("/api/v1/auth/login", {
            "username": username,
            "password": password
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        token = res.data["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return token

    def test_health_check(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), {"status": "ok"})

    def test_auth_login_and_me(self):
        # 1. Login
        res = self.client.post("/api/v1/auth/login", {
            "username": "test_manager",
            "password": "password123"
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", res.data)
        self.assertEqual(res.data["role"], "MANAGER")

        # 2. Authenticated /auth/me
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access_token']}")
        me_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data["username"], "test_manager")

    def test_categories_and_products(self):
        self.login_user("test_manager")

        # List Categories
        cat_res = self.client.get("/api/v1/categories")
        self.assertEqual(cat_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(cat_res.data), 1)

        # List Products
        prod_res = self.client.get("/api/v1/products")
        self.assertEqual(prod_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(prod_res.data), 1)
        self.assertEqual(prod_res.data[0]["sku"], "CF-DEN-TEST")
        self.assertEqual(len(prod_res.data[0]["recipes"]), 1)

    def test_order_creation_and_checkout_stock_deduction(self):
        self.login_user("test_cashier")

        # Create Order
        order_payload = {
            "customer_name": "Anh Minh",
            "table_number": "5",
            "order_type": "DINE_IN",
            "discount_amount": 0,
            "tax_amount": 0,
            "note": "Ít đá",
            "items": [
                {
                    "product_id": self.product.id,
                    "quantity": 2,
                    "note": "Ngọt vừa"
                }
            ]
        }
        create_res = self.client.post("/api/v1/orders", order_payload, format="json")
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        order_id = create_res.data["id"]
        self.assertEqual(create_res.data["subtotal"], 50000)
        self.assertEqual(create_res.data["total_amount"], 50000)
        self.assertEqual(create_res.data["status"], "PENDING")

        # Verify initial ingredient stock
        self.ingredient.refresh_from_db()
        initial_stock = self.ingredient.stock_quantity

        # Checkout Order
        checkout_payload = {
            "payment_method": "CASH",
            "amount_paid": 60000,
        }
        checkout_res = self.client.post(f"/api/v1/orders/{order_id}/checkout", checkout_payload, format="json")
        self.assertEqual(checkout_res.status_code, status.HTTP_200_OK)
        self.assertEqual(checkout_res.data["status"], "COMPLETED")
        self.assertEqual(checkout_res.data["change_due"], 10000)

        # Verify atomic stock deduction: 2 items * 20g = 40g deducted
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.stock_quantity, initial_stock - Decimal("40.0"))

    def test_management_dashboard_and_reports(self):
        self.login_user("test_manager")

        # Dashboard metrics
        dash_res = self.client.get("/api/v1/management/dashboard/metrics")
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        self.assertIn("total_revenue", dash_res.data)
        self.assertIn("total_orders", dash_res.data)

        # Sales reports
        sales_res = self.client.get("/api/v1/management/reports/sales?period=today")
        self.assertEqual(sales_res.status_code, status.HTTP_200_OK)
        self.assertIn("items", sales_res.data)
        self.assertIn("summary", sales_res.data)

        # Audit logs
        audit_res = self.client.get("/api/v1/management/audit-logs")
        self.assertEqual(audit_res.status_code, status.HTTP_200_OK)
        self.assertIn("items", audit_res.data)
