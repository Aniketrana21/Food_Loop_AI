"""
FoodLoop AI - Base Repository
Generic, transactional CRUD repository pattern providing filtering, pagination, and soft deletion.
"""
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.utils.pagination import PaginationParams, paginate_query
from app.utils.exceptions import NotFoundError

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: str) -> Optional[ModelType]:
        query = self.db.query(self.model).filter(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first()

    def get_or_404(self, id: str, entity_name: str = "Resource") -> ModelType:
        item = self.get_by_id(id)
        if not item:
            raise NotFoundError(f"{entity_name} with ID '{id}' was not found", code=f"{entity_name.upper()}_NOT_FOUND")
        return item

    def list(
        self,
        params: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        search_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        query = self.db.query(self.model)

        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))

        if filters:
            for attr, val in filters.items():
                if val is not None and hasattr(self.model, attr):
                    query = query.filter(getattr(self.model, attr) == val)

        if params.search and search_columns:
            from sqlalchemy import or_
            conditions = []
            for col_name in search_columns:
                if hasattr(self.model, col_name):
                    col = getattr(self.model, col_name)
                    conditions.append(col.ilike(f"%{params.search}%"))
            if conditions:
                query = query.filter(or_(*conditions))

        return paginate_query(query, params, model_class=self.model)

    def create(self, **kwargs) -> ModelType:
        item = self.model(**kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, id: str, **kwargs) -> ModelType:
        item = self.get_or_404(id)
        for key, val in kwargs.items():
            if val is not None and hasattr(item, key):
                setattr(item, key, val)
        if hasattr(item, "updated_at"):
            setattr(item, "updated_at", datetime.now(timezone.utc))
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, id: str, soft: bool = True) -> bool:
        item = self.get_or_404(id)
        if soft and hasattr(item, "deleted_at"):
            setattr(item, "deleted_at", datetime.now(timezone.utc))
        else:
            self.db.delete(item)
        self.db.commit()
        return True
