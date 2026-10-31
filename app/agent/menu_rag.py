"""
Menu search and matching utility.
"""
import json
from pathlib import Path
from typing import List, Dict, Any


class MenuRAG:
    """Manages menu catalog and simple item search/lookup."""

    def __init__(self, menu_path: str = "menu.json"):
        self.menu_path = Path(menu_path)
        self.items: List[Dict[str, Any]] = []
        self.load_menu()

    def load_menu(self):
        if self.menu_path.exists():
            with open(self.menu_path, "r", encoding="utf-8") as f:
                self.items = json.load(f)
        else:
            self.items = []

    def get_all(self) -> List[Dict[str, Any]]:
        return self.items

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Simple keyword ranking over menu items."""
        query_words = set(query.lower().split())
        scored = []
        for item in self.items:
            target = f"{item.get('name', '')} {item.get('description', '')} {item.get('category', '')}".lower()
            score = sum(1 for w in query_words if w in target)
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]] or self.items[:top_k]

    def find_item_by_name(self, name: str) -> Dict[str, Any] | None:
        target = name.strip().lower()
        for item in self.items:
            if item.get("name", "").lower() == target:
                return item
        for item in self.items:
            if target in item.get("name", "").lower() or item.get("name", "").lower() in target:
                return item
        return None


_menu_instance = None


def get_menu() -> MenuRAG:
    global _menu_instance
    if _menu_instance is None:
        _menu_instance = MenuRAG()
    return _menu_instance
