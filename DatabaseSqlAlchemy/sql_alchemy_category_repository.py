from datetime import datetime
from typing import List, Optional

from DTO.category_DTO import CategoryDTO
from Models.category import Category, CalendarColor
from DatabaseSqlAlchemy.interfaces import ICategoryRepository
from DatabaseSqlAlchemy.exceptions import RecordAlreadyExistsError, db_error_handler, RecordNotFoundError


class SqlAlchemyCategoryRepository(ICategoryRepository):
    def __init__(self, session):
        self.session = session

    @db_error_handler
    def add(self, category_dto: CategoryDTO) -> int:
        existing_category = self.session.query(Category).filter(
            Category.name == category_dto.name
        ).first()


        if existing_category:
            if not existing_category.is_deleted:
                raise RecordAlreadyExistsError(f"Kategoria '{category_dto.name}' już istnieje!")

            existing_category.is_deleted = False
            existing_category.updated_at = datetime.now()
            existing_category.color = category_dto.color
            existing_category.sync_enabled = category_dto.sync_enabled
            self.session.commit()
            return existing_category.id

        new_category = Category(
            name=category_dto.name,
            color=category_dto.color,
            sync_enabled=category_dto.sync_enabled,
            is_deleted=False,
            updated_at=datetime.now()
        )

        self.session.add(new_category)
        self.session.commit()
        return new_category.id

    @db_error_handler
    def update(self, category_dto: CategoryDTO) -> None:

        existing_category = self.session.get(Category, category_dto.id)

        if not existing_category:
            raise RecordNotFoundError(f"Nie można zaktualizować. Kategoria {category_dto.name} nie istnieje.")
        if existing_category.is_deleted:
            raise RecordNotFoundError(f"Kategoria o ID {category_dto.id} zostało usunięte i nie można go edytować.")

        existing_category.updated_at = datetime.now()
        existing_category.name = category_dto.name
        existing_category.sync_enabled = category_dto.sync_enabled
        existing_category.color = category_dto.color
        self.session.commit()

    @db_error_handler
    def delete(self, category_id: int) -> None:
        category = self.session.get(Category, category_id)
        if not category or category.is_deleted:
            raise RecordNotFoundError(f"Kategoria o ID {category_id} nie istnieje!")

        category.updated_at = datetime.now()
        category.is_deleted = True
        self.session.commit()

    @db_error_handler
    def get_all(self) -> List[CategoryDTO]:
        categories = self.session.query(Category).filter(Category.is_deleted == False).all()
        return [self._map_to_dto(c) for c in categories]

    @db_error_handler
    def get_by_id(self, category_id: int) -> Optional[CategoryDTO]:
        if not category_id:
            return None

        category = self.session.get(Category, category_id)

        if not category or category.is_deleted:
            return None

        return self._map_to_dto(category)


    def _map_to_dto(self, category: Category) -> CategoryDTO:
        return CategoryDTO(
            id=category.id,
            name=category.name,
            color=category.color,
            sync_enabled=category.sync_enabled
        )