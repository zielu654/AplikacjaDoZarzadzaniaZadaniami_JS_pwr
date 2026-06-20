from typing import List, Optional

from DTO.CategoryDTO import CategoryDTO


class CategoryController:
    def __init__(self, category_repo: any):
        self._category_repo = category_repo

    def create_category(self, name: str, color_hex: str, is_syncable: bool = True) -> int:
        """Tworzy nową kategorię (np. Praca, Studia, Dom) i zwraca jej ID"""
        if not name.strip():
            raise ValueError("Nazwa kategorii nie może być pusta!")
        pass

    def edit_category(self, category_id: int, name: str, color_hex: str, is_syncable: bool) -> None:
        """Modyfikuje parametry istniejącej kategorii"""
        pass

    def delete_category(self, category_id: int, cascade: bool = False) -> None:
        """
        Usuwa kategorię.
        Jeśli cascade=True, oznacza jako usunięte też wszystkie zadania z tej kategorii.
        Jeśli cascade=False, zadania dostają category_id = None.
        """
        pass

    def get_all_categories(self) -> List[CategoryDTO]:
        """Pobiera wszystkie kategorie (np. do wypełnienia rozwijanej listy / ComboBox w GUI)"""
        pass

    def get_category_by_id(self, category_id: int) -> Optional[CategoryDTO]:
        """Pobiera szczegóły jednej kategorii (np. żeby wyciągnąć jej kolor w GUI)"""
        pass
