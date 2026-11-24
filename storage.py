import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from models import InventoryManager, Product


def save_inventory(products, filepath="inventory.json"):
    path = Path(filepath)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump([p.to_dict() for p in products], stream, indent=2, ensure_ascii=False)
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def load_inventory(filepath="inventory.json", notify=None):
    path = Path(filepath)
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError("Expected a list of products.")
        manager = InventoryManager(Product.from_dict(row) for row in rows)
        return list(manager.products.values())
    except FileNotFoundError:
        save_inventory([], path)
    except (ValueError, TypeError) as error:
        backup = path.with_name(f"{path.stem}-{uuid4().hex[:8]}.bak")
        path.rename(backup)
        save_inventory([], path)
        if notify:
            notify(f"Opened an empty inventory. Original data saved as {backup.name}.")
    return []
