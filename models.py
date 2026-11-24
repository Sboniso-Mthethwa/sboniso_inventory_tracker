from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Product:
    item_id: str
    name: str
    category: str
    cost_price: Decimal
    selling_price: Decimal
    quantity: int
    reorder_level: int

    def __post_init__(self):
        for field in ("item_id", "name", "category"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Enter a {field.replace('_', ' ')}.")
            object.__setattr__(self, field, value.strip())
        for field in ("cost_price", "selling_price"):
            try:
                price = Decimal(str(getattr(self, field)))
                if not price.is_finite() or price < 0 or price != price.quantize(Decimal(".01")):
                    raise InvalidOperation
            except InvalidOperation:
                raise ValueError(f"Enter a non-negative {field.replace('_', ' ')} with up to two decimals.")
            object.__setattr__(self, field, price)
        for field in ("quantity", "reorder_level"):
            value = str(getattr(self, field)).strip()
            if not value.isdecimal():
                raise ValueError(f"Enter a whole number of zero or more for {field.replace('_', ' ')}.")
            object.__setattr__(self, field, int(value))

    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    def profit_per_unit(self):
        return self.selling_price - self.cost_price

    def to_dict(self):
        return dict(asdict(self), cost_price=str(self.cost_price), selling_price=str(self.selling_price))

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class InventoryManager:
    def __init__(self, products=()):
        self.products = {}
        for product in products:
            self.add_product(product)

    def add_product(self, product):
        if product.item_id in self.products:
            raise ValueError("This item ID already exists.")
        self.products[product.item_id] = product

    def update_product(self, product):
        if product.item_id not in self.products:
            raise ValueError("Item no longer exists.")
        self.products[product.item_id] = product

    def adjust_stock(self, item_id, delta):
        product = self.products[item_id]
        self.update_product(replace(product, quantity=product.quantity + delta))

    def delete_product(self, item_id):
        del self.products[item_id]

    def get_low_stock_items(self):
        return [p for p in self.products.values() if p.is_low_stock()]

    def total_inventory_value(self):
        return sum((p.cost_price * p.quantity for p in self.products.values()), Decimal(0))
