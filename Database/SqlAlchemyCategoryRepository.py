from datetime import datetime
from typing import List

from Models.Category import Category
from Database.Interfaces import ICategoryRepository
from Database.exceptions import RecordAlreadyExistsError, db_error_handler, RecordNotFoundError


class SqlAlchemyCategoryRepository(ICategoryRepository):
    def __init__(self, session):
        self.session = session

    @db_error_handler
    def add(self, category: Category) -> int:
        existing_category = self.session.query(Category).filter(
            Category.name == category.name
        ).first()

        if existing_category:
            if not existing_category.is_deleted:
                raise RecordAlreadyExistsError(f"Kategoria '{category.name}' już istnieje!")

            existing_category.is_deleted = False
            existing_category.updated_at = datetime.now()
            existing_category.color = category.color
            existing_category.is_synced = category.is_synced
            self.session.commit()
            return existing_category.id

        category.updated_at = datetime.now()
        self.session.add(category)
        self.session.commit()
        return category.id

    @db_error_handler
    def update(self, category: Category) -> None:

        existing_category = self.session.get(Category, category.id)

        if not existing_category:
            raise RecordNotFoundError(f"Nie można zaktualizować. Wydarzenie {category.name} nie istnieje.")
        if existing_category.is_deleted:
            raise RecordNotFoundError(f"Wydarzenie o ID {category.id} zostało usunięte i nie można go edytować.")

        category.updated_at = datetime.now()
        self.session.merge(category)
        self.session.commit()

    @db_error_handler
    def delete(self, category_id: int) -> None:
        category = self.session.get(Category, category_id)
        if not category or category.is_deleted:
            raise RecordNotFoundError(f"Event o ID {category_id} nie istnieje!")

        category.updated_at = datetime.now()
        category.is_deleted = True
        self.session.commit()

    @db_error_handler
    def get_all(self) -> List[Category]:
        return self.session.query(Category).filter(Category.is_deleted == False).all()