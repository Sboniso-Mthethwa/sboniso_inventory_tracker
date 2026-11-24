from pathlib import Path
from uuid import uuid4

# The academy workspace can select another exercise's Python environment.
# Direct launches on this PC use the tracker's installed desktop runtime.
if __name__ == "__main__":
    import os
    import subprocess
    import sys

    if os.name == "nt" and "LOCALAPPDATA" in os.environ:
        runtime = Path(os.environ["LOCALAPPDATA"]) / "FletRuntimes/inventory-0.28.3/Scripts/python.exe"
        if runtime.is_file() and Path(sys.executable) != runtime:
            raise SystemExit(subprocess.call([str(runtime), "-B", str(Path(__file__).resolve()), *sys.argv[1:]]))

import flet as ft

from models import InventoryManager, Product
from storage import load_inventory, save_inventory


DATA = Path(__file__).with_name("inventory.json")
CATEGORIES = ["Groceries", "Household", "Stationery", "Clothing", "Other"]
ALL_CATEGORIES = "__all_categories__"
INK = "#152D37"
PAPER = "#F6F4EE"
TEAL = "#11685C"


def panel(content, **options):
    return ft.Container(content, bgcolor="white", border=ft.border.all(1, "#D9DFDB"),
                        border_radius=16, padding=18, **options)


def heading(text):
    return ft.Text(text, size=20, weight=ft.FontWeight.BOLD, color=INK)


def main(page: ft.Page):
    page.title = "MoonwalkerSir's Inventory Tracker"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=TEAL)
    page.bgcolor = PAPER
    page.padding = 20
    messages = []
    try:
        manager = InventoryManager(load_inventory(DATA, messages.append))
    except OSError as error:
        page.add(ft.Text("Inventory could not be opened", size=24), ft.Text(str(error)))
        return

    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14)
    rows = ft.ResponsiveRow(spacing=14, run_spacing=14)
    search = ft.TextField(label="Search products by name", prefix_icon=ft.Icons.SEARCH, col={"xs": 12, "sm": 8})
    category = ft.Dropdown(label="Filter by category", value=ALL_CATEGORIES, col={"xs": 12, "sm": 4})

    def notify(message):
        page.open(ft.SnackBar(ft.Text(message)))

    def commit(change, message, destination=None):
        nonlocal manager
        candidate = InventoryManager(manager.products.values())
        try:
            change(candidate)
            save_inventory(candidate.products.values(), DATA)
        except (ValueError, KeyError, OSError) as error:
            notify(f"Could not save. {error}")
            return
        manager = candidate
        show(nav.selected_index if destination is None else destination)
        notify(message)

    def confirm_delete(product):
        def remove(event):
            page.close(dialog)
            commit(lambda m: m.delete_product(product.item_id), "Product deleted.")

        dialog = ft.AlertDialog(title=ft.Text(f"Delete {product.name}?"), actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
            ft.TextButton("Delete", on_click=remove)])
        page.open(dialog)

    def stock_card(p):
        def adjust(delta):
            return lambda e: commit(lambda m: m.adjust_stock(p.item_id, delta), "Stock updated.")

        low = p.is_low_stock()
        details = [
            ft.Row([ft.Text(p.category, color=TEAL, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Container(ft.Text("Reorder" if low else "In stock", size=12,
                                         color="#85320D" if low else TEAL),
                                 bgcolor="#FFE1CC" if low else "#E1F2E9",
                                 border_radius=12, padding=6)]),
            heading(p.name),
            ft.Text(f"Cost R{p.cost_price:,.2f}  ·  Sell R{p.selling_price:,.2f}"),
            ft.Divider(height=1, color="#D9DFDB"),
            ft.Row([ft.Text(f"{p.quantity} on hand", weight=ft.FontWeight.BOLD, color=INK),
                    ft.Text(f"Reorder at {p.reorder_level}", size=12)], wrap=True),
        ]
        details.append(ft.Row([
            ft.IconButton(ft.Icons.REMOVE, tooltip="Remove one unit", disabled=p.quantity == 0, on_click=adjust(-1)),
            ft.IconButton(ft.Icons.ADD, tooltip="Add one unit", on_click=adjust(1)),
            ft.TextButton("Edit", on_click=lambda e: show(1, p)),
            ft.TextButton("Delete", on_click=lambda e: confirm_delete(p)),
        ], wrap=True))
        return panel(ft.Column(details, spacing=10), col={"xs": 12, "sm": 6, "lg": 4, "xl": 3})

    def filter_rows(event=None):
        matches = [p for p in manager.products.values()
                   if (category.value == ALL_CATEGORIES or category.value == p.category)
                   and search.value.strip().casefold() in p.name.casefold()]
        rows.controls = [stock_card(p) for p in sorted(matches, key=lambda p: p.name.casefold())]
        if not matches:
            hint = "No matching products" if manager.products else "Your shelves are empty"
            action = ft.Text("Try another name or category.") if manager.products else ft.FilledButton(
                "Add your first product", icon=ft.Icons.ADD, on_click=lambda e: show(1))
            rows.controls.append(panel(ft.Column([
                ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=TEAL, size=38), heading(hint), action
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center))
        if event:
            page.update()

    search.value = ""
    search.on_change = category.on_change = filter_rows

    def form(product):
        fields = {}
        labels = dict(name="Product name", cost_price="Cost price (R)", selling_price="Selling price (R)",
                      quantity="Quantity on hand", reorder_level="Reorder level")
        for key, label in labels.items():
            default = "0" if key in ("quantity", "reorder_level") else ""
            fields[key] = ft.TextField(label=label, value=str(getattr(product, key, default)))
        choices = sorted(set(CATEGORIES) | {p.category for p in manager.products.values()})
        group = ft.Dropdown(label="Category", value=getattr(product, "category", "Other"),
                            options=[ft.dropdown.Option(c) for c in choices])
        feedback = ft.Text(color="#A02818")

        def save(event):
            try:
                item = Product(item_id=product.item_id if product else uuid4().hex, category=group.value,
                               **{key: field.value for key, field in fields.items()})
            except ValueError as error:
                feedback.value = str(error)
                page.update()
                return
            def apply(m):
                if product:
                    m.update_product(item)
                else:
                    m.add_product(item)
            commit(apply, "Product saved.", 0)

        def pair(left, right):
            for field in (left, right):
                field.col = {"xs": 12, "sm": 6}
            return ft.ResponsiveRow([left, right])

        return [panel(ft.Column([
            heading("Product details"), pair(fields["name"], group),
            heading("Pricing"), pair(fields["cost_price"], fields["selling_price"]),
            heading("Stock levels"), pair(fields["quantity"], fields["reorder_level"]),
            feedback, ft.Row([ft.FilledButton("Save product", icon=ft.Icons.CHECK, on_click=save),
                              ft.TextButton("Cancel", on_click=lambda e: show(0))])
        ], spacing=14))]

    def show(index, product=None):
        nav.selected_index = index
        title = ["Inventory", "Edit product" if product else "Add product", "Low-stock alerts"][index]
        hero = ft.Row([
            ft.Container(ft.Icon([ft.Icons.STOREFRONT, ft.Icons.EDIT, ft.Icons.NOTIFICATIONS][index],
                                 size=30, color=INK), padding=12, bgcolor="#D9EE96", border_radius=14),
            ft.Text(title, size=32, color="white", weight=ft.FontWeight.BOLD, expand=True)
        ], spacing=16)
        controls = [ft.Container(hero, padding=22, border_radius=18,
                                 gradient=ft.LinearGradient(colors=[INK, "#205B54"]))]
        if index == 0:
            totals = [("Products", str(len(manager.products))),
                      ("Stock value at cost", f"R{manager.total_inventory_value():,.2f}"),
                      ("Need reordering", str(len(manager.get_low_stock_items())))]
            styles = [(ft.Icons.INVENTORY_2_OUTLINED, "#DFEBFA"), (ft.Icons.PAYMENTS_OUTLINED, "#DDF0DF"),
                      (ft.Icons.NOTIFICATIONS_OUTLINED, "#FFE4CE")]
            controls.append(ft.ResponsiveRow([
                ft.Container(ft.Column([ft.Row([ft.Icon(icon, size=19, color=INK), ft.Text(k, color=INK)]),
                                        ft.Text(v, size=28, color=INK, weight=ft.FontWeight.BOLD)]),
                             bgcolor=tint, padding=16, border_radius=14, col={"xs": 12, "sm": 4})
                for (k, v), (icon, tint) in zip(totals, styles)]))
            options = sorted({p.category for p in manager.products.values()})
            category.options = [ft.dropdown.Option(ALL_CATEGORIES, "All categories")] + [ft.dropdown.Option(c) for c in options]
            if category.value not in options:
                category.value = ALL_CATEGORIES
            filter_rows()
            controls.extend([heading("Product catalogue"), panel(ft.ResponsiveRow([search, category])), rows])
        elif index == 1:
            controls.extend(form(product))
        else:
            alerts = sorted(manager.get_low_stock_items(), key=lambda p: (p.quantity, p.name.casefold()))
            controls.append(ft.ResponsiveRow([stock_card(p) for p in alerts], spacing=14, run_spacing=14)
                            if alerts else panel(ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=TEAL),
                ft.Text("No products need reordering.", expand=True)])))
        body.controls = controls
        page.update()

    nav = ft.NavigationBar(bgcolor="white", indicator_color="#D9EE96", destinations=[
        ft.NavigationBarDestination(icon=ft.Icons.INVENTORY_2, label="Inventory"),
        ft.NavigationBarDestination(icon=ft.Icons.ADD_BOX, label="Product"),
        ft.NavigationBarDestination(icon=ft.Icons.NOTIFICATIONS, label="Alerts")],
        on_change=lambda e: show(e.control.selected_index))
    page.navigation_bar = nav
    page.add(body)
    show(0)
    for message in messages:
        notify(message)


if __name__ == "__main__":
    ft.app(target=main)
