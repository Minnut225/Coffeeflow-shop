from decimal import Decimal
from django.core.management.base import BaseCommand
from api.models import (
    User,
    UserRole,
    Category,
    Product,
    Ingredient,
    Recipe,
)

class Command(BaseCommand):
    help = 'Seeds initial default users, categories, products, ingredients, and recipes.'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding process...")

        # 1. Seed Users
        users_data = [
            {"username": "manager", "full_name": "Nguyễn Mai Lan", "role": UserRole.MANAGER, "password": "password123"},
            {"username": "cashier", "full_name": "Trần Thu Ngân", "role": UserRole.CASHIER, "password": "password123"},
            {"username": "manager1", "full_name": "Manager One", "role": UserRole.MANAGER, "password": "password123"},
            {"username": "cashier1", "full_name": "Cashier One", "role": UserRole.CASHIER, "password": "password123"},
        ]

        for u in users_data:
            user, created = User.objects.get_or_create(
                username=u["username"],
                defaults={
                    "full_name": u["full_name"],
                    "role": u["role"],
                    "is_active": True,
                }
            )
            if created or not user.hashed_password:
                user.set_password(u["password"])
                user.save()
                self.stdout.write(f"Created user: {u['username']}")
            else:
                self.stdout.write(f"User already exists: {u['username']}")

        # 2. Seed Categories
        categories_data = [
            {"name": "Cà phê truyền thống", "display_order": 1},
            {"name": "Cà phê máy", "display_order": 2},
            {"name": "Trà & Macchiato", "display_order": 3},
            {"name": "Bánh ngọt", "display_order": 4},
        ]
        cat_map = {}
        for c in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=c["name"],
                defaults={"display_order": c["display_order"], "is_active": True}
            )
            cat_map[c["name"]] = cat

        # 3. Seed Ingredients
        ingredients_data = [
            {"name": "Cà phê Robusta Đắk Lắk", "sku": "ING-ROB-01", "unit": "g", "stock_quantity": Decimal("25000.0"), "min_stock_level": Decimal("2000.0"), "cost_per_unit": 180},
            {"name": "Cà phê Arabica Cầu Đất", "sku": "ING-ARA-02", "unit": "g", "stock_quantity": Decimal("20000.0"), "min_stock_level": Decimal("2000.0"), "cost_per_unit": 250},
            {"name": "Sữa đặc Phương Nam", "sku": "ING-SUA-03", "unit": "g", "stock_quantity": Decimal("15000.0"), "min_stock_level": Decimal("1500.0"), "cost_per_unit": 80},
            {"name": "Sữa tươi Dalat Milk thanh trùng", "sku": "ING-MILK-04", "unit": "ml", "stock_quantity": Decimal("30000.0"), "min_stock_level": Decimal("3000.0"), "cost_per_unit": 45},
            {"name": "Kem béo mặn Cố Đô", "sku": "ING-KEM-05", "unit": "g", "stock_quantity": Decimal("8000.0"), "min_stock_level": Decimal("800.0"), "cost_per_unit": 120},
            {"name": "Trà lài thượng hạng", "sku": "ING-TRA-06", "unit": "g", "stock_quantity": Decimal("10000.0"), "min_stock_level": Decimal("1000.0"), "cost_per_unit": 150},
        ]
        ing_map = {}
        for ing in ingredients_data:
            obj, _ = Ingredient.objects.get_or_create(
                sku=ing["sku"],
                defaults={
                    "name": ing["name"],
                    "unit": ing["unit"],
                    "stock_quantity": ing["stock_quantity"],
                    "min_stock_level": ing["min_stock_level"],
                    "cost_per_unit": ing["cost_per_unit"],
                }
            )
            ing_map[ing["sku"]] = obj

        # 4. Seed Products
        products_data = [
            {
                "category": cat_map["Cà phê truyền thống"],
                "name": "Cà phê đen đá Đắk Lắk",
                "sku": "CF-DEN-01",
                "price": 25000,
                "cost_price": 5000,
                "description": "Cà phê Robusta Đắk Lắk pha phin truyền thống đậm đà.",
                "recipes": [{"sku": "ING-ROB-01", "qty": Decimal("25.0")}],
            },
            {
                "category": cat_map["Cà phê truyền thống"],
                "name": "Cà phê sữa đá Sài Gòn",
                "sku": "CF-SUA-02",
                "price": 29000,
                "cost_price": 7500,
                "description": "Cà phê Robusta kết hợp sữa đặc Phương Nam ngọt ngào.",
                "recipes": [
                    {"sku": "ING-ROB-01", "qty": Decimal("25.0")},
                    {"sku": "ING-SUA-03", "qty": Decimal("30.0")},
                ],
            },
            {
                "category": cat_map["Cà phê truyền thống"],
                "name": "Cà phê muối xứ Huế",
                "sku": "CF-MUOI-03",
                "price": 35000,
                "cost_price": 10000,
                "description": "Lớp kem béo mặn sánh mịn phủ trên nền cà phê phin đậm vị.",
                "recipes": [
                    {"sku": "ING-ROB-01", "qty": Decimal("25.0")},
                    {"sku": "ING-SUA-03", "qty": Decimal("20.0")},
                    {"sku": "ING-KEM-05", "qty": Decimal("40.0")},
                ],
            },
            {
                "category": cat_map["Cà phê máy"],
                "name": "Espresso Arabica Cầu Đất",
                "sku": "ESP-SINGLE-04",
                "price": 30000,
                "cost_price": 6000,
                "description": "Single shot Espresso chiết xuất từ 100% hạt Arabica Cầu Đất.",
                "recipes": [{"sku": "ING-ARA-02", "qty": Decimal("18.0")}],
            },
            {
                "category": cat_map["Cà phê máy"],
                "name": "Latte Cầu Đất",
                "sku": "LATTE-05",
                "price": 45000,
                "cost_price": 12000,
                "description": "Espresso kết hợp sữa tươi Dalat Milk đánh nóng bồng bềnh.",
                "recipes": [
                    {"sku": "ING-ARA-02", "qty": Decimal("18.0")},
                    {"sku": "ING-MILK-04", "qty": Decimal("200.0")},
                ],
            },
            {
                "category": cat_map["Trà & Macchiato"],
                "name": "Trà lài Macchiato kem mặn",
                "sku": "TRA-MAC-06",
                "price": 39000,
                "cost_price": 9500,
                "description": "Trà hoa lài thanh mát cùng lớp macchiato kem béo mềm mịn.",
                "recipes": [
                    {"sku": "ING-TRA-06", "qty": Decimal("10.0")},
                    {"sku": "ING-KEM-05", "qty": Decimal("50.0")},
                ],
            },
        ]

        for p_info in products_data:
            recipes = p_info.pop("recipes", [])
            prod, created = Product.objects.get_or_create(
                sku=p_info["sku"],
                defaults=p_info,
            )
            if created or not prod.recipes.exists():
                for r in recipes:
                    Recipe.objects.create(
                        product=prod,
                        ingredient=ing_map[r["sku"]],
                        quantity_required=r["qty"],
                    )
                self.stdout.write(f"Created product: {prod.name}")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
