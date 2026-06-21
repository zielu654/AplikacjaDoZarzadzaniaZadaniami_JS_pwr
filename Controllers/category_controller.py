from typing import List, Optional, Dict

from Controllers.exceptions import EmptyFieldError, ValidationError
from DTO.category_DTO import CategoryDTO
from DatabaseSqlAlchemy.interfaces import ICategoryRepository, IEventRepository
from Models.category import CalendarColor


class CategoryController:
    def __init__(self, category_repo: ICategoryRepository, event_repo: IEventRepository ) -> None:
        self._category_repo = category_repo
        self._event_repo = event_repo

    def create_category(self, name: str, color_hex: str, is_syncable: bool = True) -> int:
        """Tworzy nową kategorię (np. Praca, Studia, Dom) i zwraca jej ID"""
        if not name or not name.strip():
            raise EmptyFieldError("Nazwa kategorii nie może być pusta!")

        new_category = CategoryDTO(
            id=0,
            name=name.strip(),
            color_hex=color_hex,
            color_name=CalendarColor.color_hex_to_callendarColor(color_hex).display_name,
            sync_enabled=is_syncable
        )
        return self._category_repo.add(new_category)

    def edit_category(self, category_id: int, updates: Dict) -> None:
        """
        Modyfikuje wybrane parametry istniejącej kategorii.
        'updates' to słownik, np. {'name': 'Nowa nazwa', 'color_hex': '#ffffff'}
        zmienne : name; color_hex; color_name; is_syncable
        """
        category = self._category_repo.get_by_id(category_id)
        if not category:
            raise ValueError(f"Kategoria o ID {category_id} nie istnieje!")

        if 'name' in updates:
            new_name = updates['name']
            if not new_name or not str(new_name).strip():
                raise ValueError("Nazwa kategorii nie może być pusta!")
            category.name = str(new_name).strip()

        if 'color_hex' in updates:
            if all(color.hex_code != updates['color_hex'] for color in CalendarColor):
                raise ValidationError("Niepoprawny kolor!")
            category.color_hex = updates['color_hex']
            category.color_name = CalendarColor.color_hex_to_callendarColor(updates['color_hex']).display_name


        if 'color_name' in updates:
            if all(color.name != updates['color_name'] for color in CalendarColor):
                raise ValidationError("Niepoprawny kolor!")
            category.color_name = updates['color_name']
            category.color_hex = CalendarColor.color_name_to_callendarColor(updates['color_name']).display_name

        if 'is_syncable' in updates:
            category.sync_enabled = bool(updates['is_syncable'])

        self._category_repo.update(category)

    def delete_category(self, category_id: int, cascade: bool = False) -> None:
        """
        Usuwa kategorię.
        Jeśli cascade=True, oznacza jako usunięte też wszystkie zadania z tej kategorii.
        Jeśli cascade=False, zadania dostają category_id = None.
        """

        category = self._category_repo.get_by_id(category_id)
        if not category:
            raise ValueError(f"Kategoria o ID {category_id} nie istnieje!")

        if self._event_repo:
            events_in_category = self._event_repo.query().by_category(category_id).get_list()
            for event in events_in_category:
                if cascade:
                    self._event_repo.delete(event.id)
                else:
                    event.category_id = None
                    event.category = None
                    self._event_repo.update(event)

        self._category_repo.delete(category_id)

    def get_all_categories(self) -> List[CategoryDTO]:
        """Pobiera wszystkie kategorie (np. do wypełnienia rozwijanej listy / ComboBox w GUI)"""
        return self._category_repo.get_all()

    def get_category_by_id(self, category_id: int) -> Optional[CategoryDTO]:
        """Pobiera szczegóły jednej kategorii (np. żeby wyciągnąć jej kolor w GUI)"""
        return self._category_repo.get_by_id(category_id)
