"""
FoodLoop AI - SQLAlchemy 2.0 Enterprise ORM Models
Covers all 30 core platform tables with UUIDs, foreign keys, relationships,
status constraints, and auditability.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Date, ForeignKey, Text, JSON, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ====================================================================
# 1. CORE IDENTITY & ORGANIZATIONS
# ====================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), default="", nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="KITCHEN_MANAGER")  # ADMIN, KITCHEN_MANAGER, PROCESSOR, NGO, DRIVER, AUDITOR
    phone = Column(String(50), nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    _cached_org_name = Column("organization_name", String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    driver_profile = relationship("Driver", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    # Compatibility properties
    @property
    def organization_name(self):
        if self._cached_org_name:
            return self._cached_org_name
        if self.memberships and self.memberships[0].organization:
            return self.memberships[0].organization.name
        return "FoodLoop Member"

    @organization_name.setter
    def organization_name(self, value):
        self._cached_org_name = value


# Backward compatibility alias
Profile = User


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    org_type = Column(String(50), nullable=False, default="COMMERCIAL_KITCHEN")
    registration_number = Column(String(100), unique=True, nullable=False)
    tax_id = Column(String(100), nullable=True)
    license_fssai_fda = Column(String(100), nullable=True)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    kitchens = relationship("Kitchen", back_populates="organization", cascade="all, delete-orphan")
    processing_units = relationship("ProcessingUnit", back_populates="organization", cascade="all, delete-orphan")
    surplus_items = relationship("SurplusItem", back_populates="organization", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="organization", cascade="all, delete-orphan")
    drivers = relationship("Driver", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_in_org = Column(String(50), default="MEMBER", nullable=False)
    is_primary = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_org_member"),)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")

    def __init__(self, **kwargs):
        if "role" in kwargs and "role_in_org" not in kwargs:
            kwargs["role_in_org"] = kwargs.pop("role")
        super().__init__(**kwargs)

    @property
    def role(self):
        return self.role_in_org

    @role.setter
    def role(self, val):
        self.role_in_org = val



# ====================================================================
# 2. FACILITIES & OPERATIONS
# ====================================================================

class Kitchen(Base):
    __tablename__ = "kitchens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    daily_meal_capacity = Column(Integer, default=500, nullable=False)
    storage_specs = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="kitchens")
    menus = relationship("Menu", back_populates="kitchen", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="kitchen", cascade="all, delete-orphan")
    batches = relationship("ProductionBatch", back_populates="kitchen", cascade="all, delete-orphan")
    waste_records = relationship("WasteRecord", back_populates="kitchen", cascade="all, delete-orphan")

    # Compatibility properties
    @property
    def capacity(self):
        return self.daily_meal_capacity

    @property
    def contact_name(self):
        return (self.storage_specs or {}).get("contact_name", "Executive Chef")

    @contact_name.setter
    def contact_name(self, value):
        specs = dict(self.storage_specs or {})
        specs["contact_name"] = value
        self.storage_specs = specs

    @property
    def contact_phone(self):
        return (self.storage_specs or {}).get("contact_phone", "+1-555-0100")

    @contact_phone.setter
    def contact_phone(self, value):
        specs = dict(self.storage_specs or {})
        specs["contact_phone"] = value
        self.storage_specs = specs

    @property
    def has_cold_storage(self):
        return (self.storage_specs or {}).get("has_cold_storage", True)

    @has_cold_storage.setter
    def has_cold_storage(self, value):
        specs = dict(self.storage_specs or {})
        specs["has_cold_storage"] = value
        self.storage_specs = specs

    @property
    def has_hot_holding(self):
        return (self.storage_specs or {}).get("has_hot_holding", True)

    @has_hot_holding.setter
    def has_hot_holding(self, value):
        specs = dict(self.storage_specs or {})
        specs["has_hot_holding"] = value
        self.storage_specs = specs

    @property
    def facility_type(self):
        return (self.storage_specs or {}).get("facility_type", "COMMERCIAL_KITCHEN")

    @facility_type.setter
    def facility_type(self, value):
        specs = dict(self.storage_specs or {})
        specs["facility_type"] = value
        self.storage_specs = specs

    @property
    def certifications(self):
        return (self.storage_specs or {}).get("certifications", ["HACCP", "ServSafe"])

    @certifications.setter
    def certifications(self, value):
        specs = dict(self.storage_specs or {})
        specs["certifications"] = value
        self.storage_specs = specs

    @property
    def status(self):
        return "ACTIVE" if self.is_active else "INACTIVE"

    @status.setter
    def status(self, value):
        self.is_active = (value == "ACTIVE")



class ProcessingUnit(Base):
    __tablename__ = "processing_units"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    processing_type = Column(String(100), nullable=False)
    daily_capacity_kg = Column(Float, default=2000.0, nullable=False)
    cold_tank_capacity_liters = Column(Float, default=5000.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="processing_units")
    inventory = relationship("Inventory", back_populates="processing_unit", cascade="all, delete-orphan")
    raw_materials = relationship("FpuRawMaterial", back_populates="processing_unit", cascade="all, delete-orphan")
    production_batches = relationship("FpuProductionBatch", back_populates="processing_unit", cascade="all, delete-orphan")
    alert_thresholds = relationship("FpuExpiryAlertThreshold", back_populates="processing_unit", cascade="all, delete-orphan")

    # Compatibility properties for Phase 3 & Phase 14 schemas
    @property
    def unit_type(self):
        return self.processing_type

    @unit_type.setter
    def unit_type(self, val):
        self.processing_type = val

    @property
    def daily_throughput_capacity_kg(self):
        return self.daily_capacity_kg

    @daily_throughput_capacity_kg.setter
    def daily_throughput_capacity_kg(self, val):
        self.daily_capacity_kg = val

    @property
    def contact_person(self):
        return getattr(self, "_contact_person", "Facility Lead")

    @contact_person.setter
    def contact_person(self, val):
        self._contact_person = val

    @property
    def contact_phone(self):
        return getattr(self, "_contact_phone", "+1-555-4000")

    @contact_phone.setter
    def contact_phone(self, val):
        self._contact_phone = val

    @property
    def accepted_feedstocks(self):
        return getattr(self, "_accepted_feedstocks", ["PRODUCE", "GRAINS", "DAIRY"])

    @accepted_feedstocks.setter
    def accepted_feedstocks(self, val):
        self._accepted_feedstocks = val

    @property
    def output_products(self):
        return getattr(self, "_output_products", ["PUREE", "CANNED_GOODS", "DEHYDRATED"])

    @output_products.setter
    def output_products(self, val):
        self._output_products = val


# ====================================================================
# 2B. FOOD PROCESSING UNIT (PHASE 14) MODELS
# ====================================================================

class FpuRawMaterial(Base):
    __tablename__ = "fpu_raw_materials"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    processing_unit_id = Column(String(36), ForeignKey("processing_units.id", ondelete="CASCADE"), nullable=False)
    material_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, default="PRODUCE")  # PRODUCE, GRAINS, DAIRY, LIQUIDS, PACKAGING, SEASONINGS, BAKERY_TRIMMINGS, MEAT
    lot_number = Column(String(100), nullable=False, index=True)
    initial_quantity = Column(Float, nullable=False)
    current_quantity = Column(Float, nullable=False)
    unit = Column(String(50), default="kg", nullable=False)
    storage_condition = Column(String(100), default="REFRIGERATED", nullable=False)  # REFRIGERATED, DRY_STORAGE, FROZEN, AMBIENT
    storage_location = Column(String(100), default="Cold Storage Bay 1", nullable=False)
    harvest_or_mfg_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False, index=True)
    quality_status = Column(String(50), default="APPROVED", nullable=False)  # APPROVED, UNDER_REVIEW, REJECTED, QUARANTINED
    packaging_condition = Column(String(50), default="INTACT", nullable=False)  # INTACT, DAMAGED_PACKAGING, LEAKING, SEAL_COMPROMISED
    damaged_quantity = Column(Float, default=0.0, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    disposition_action = Column(String(100), nullable=True)  # ANIMAL_FEED_VALORIZATION, COMPOSTING, SAFE_DISPOSAL, RETURN_SUPPLIER
    supplier = Column(String(255), nullable=True)
    cost_per_unit = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="AVAILABLE", nullable=False)  # AVAILABLE, ALLOCATED, DEPLETED, EXPIRED, QUARANTINED, REJECTED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    processing_unit = relationship("ProcessingUnit", back_populates="raw_materials")
    usages = relationship("FpuBatchMaterialUsage", back_populates="raw_material", cascade="all, delete-orphan")


class FpuProductionBatch(Base):
    __tablename__ = "fpu_production_batches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    processing_unit_id = Column(String(36), ForeignKey("processing_units.id", ondelete="CASCADE"), nullable=False)
    batch_number = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), default="PROCESSED_CANNING", nullable=False)  # PROCESSED_CANNING, DEHYDRATED, PUREE, BAKERY_REPROCESSED, JUICE_BEVERAGE, VALUE_ADDED
    planned_quantity = Column(Float, nullable=False)
    actual_quantity = Column(Float, default=0.0, nullable=False)
    unit = Column(String(50), default="kg", nullable=False)
    manufacturing_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False, index=True)
    quality_status = Column(String(50), default="PASSED", nullable=False)  # PASSED, UNDER_REVIEW, REJECTED, DAMAGED_PACKAGING, QUARANTINED
    packaging_condition = Column(String(50), default="INTACT", nullable=False)  # INTACT, DAMAGED_PACKAGING, SEAL_FAILURE, DEFECTIVE_LABEL, DENTED_CONTAINER
    damaged_packaging_units = Column(Float, default=0.0, nullable=False)
    rejected_quantity = Column(Float, default=0.0, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    disposition_action = Column(String(100), nullable=True)  # RE_PROCESS, ANIMAL_FEED_VALORIZATION, COMPOST_BIOGAS, HAZARDOUS_DISPOSAL
    yield_percentage = Column(Float, default=100.0, nullable=False)
    surplus_quantity = Column(Float, default=0.0, nullable=False)
    redistributable_stock = Column(Float, default=0.0, nullable=False)
    redistribution_status = Column(String(50), default="NOT_DECLARED", nullable=False)  # NOT_DECLARED, AVAILABLE_FOR_REDISTRIBUTION, ALLOCATED_TO_DONATION, DISPATCHED, DELIVERED
    status = Column(String(50), default="COMPLETED", nullable=False)  # PLANNED, IN_PRODUCTION, QUALITY_CONTROL, COMPLETED, QUARANTINED, REJECTED
    operator_notes = Column(Text, nullable=True)
    qc_officer = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    processing_unit = relationship("ProcessingUnit", back_populates="production_batches")
    raw_material_usages = relationship("FpuBatchMaterialUsage", back_populates="batch", cascade="all, delete-orphan")
    surplus_items = relationship("SurplusItem", back_populates="fpu_batch")


class FpuBatchMaterialUsage(Base):
    __tablename__ = "fpu_batch_material_usages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    batch_id = Column(String(36), ForeignKey("fpu_production_batches.id", ondelete="CASCADE"), nullable=False)
    raw_material_id = Column(String(36), ForeignKey("fpu_raw_materials.id", ondelete="RESTRICT"), nullable=False)
    quantity_used = Column(Float, nullable=False)
    unit = Column(String(50), default="kg", nullable=False)
    fefo_sequence_order = Column(Integer, default=1, nullable=False)
    lot_expiry_at_consumption = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    batch = relationship("FpuProductionBatch", back_populates="raw_material_usages")
    raw_material = relationship("FpuRawMaterial", back_populates="usages")


class FpuExpiryAlertThreshold(Base):
    __tablename__ = "fpu_expiry_alert_thresholds"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    processing_unit_id = Column(String(36), ForeignKey("processing_units.id", ondelete="CASCADE"), nullable=True)
    target_type = Column(String(50), default="CATEGORY", nullable=False)  # CATEGORY, PRODUCT, RAW_MATERIAL
    target_name = Column(String(100), nullable=False)  # DAIRY, PRODUCE, CANNED_GOODS, etc.
    warning_threshold_days = Column(Float, default=7.0, nullable=False)  # e.g., 7 days
    urgent_threshold_days = Column(Float, default=3.0, nullable=False)   # e.g., 3 days
    critical_threshold_days = Column(Float, default=1.0, nullable=False) # e.g., 1 day
    is_active = Column(Boolean, default=True, nullable=False)
    custom_safety_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    processing_unit = relationship("ProcessingUnit", back_populates="alert_thresholds")


# ====================================================================
# 3. MENUS & RECIPES
# ====================================================================

class Menu(Base):
    __tablename__ = "menus"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    kitchen_id = Column(String(36), ForeignKey("kitchens.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    service_date = Column(DateTime, nullable=False)
    meal_service = Column(String(50), nullable=False)  # BREAKFAST, LUNCH, DINNER, SNACK
    planned_headcount = Column(Integer, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    kitchen = relationship("Kitchen", back_populates="menus")
    items = relationship("MenuItem", back_populates="menu", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        self._organization_id = kwargs.pop("organization_id", None)
        self._season_or_cycle = kwargs.pop("season_or_cycle", "SEASONAL_CYCLE")
        self._is_active = kwargs.pop("is_active", True)
        if "service_date" not in kwargs:
            from datetime import datetime, timezone
            kwargs["service_date"] = datetime.now(timezone.utc)
        if "meal_service" not in kwargs:
            kwargs["meal_service"] = "LUNCH"
        if "planned_headcount" not in kwargs:
            kwargs["planned_headcount"] = 500
        super().__init__(**kwargs)

    @property
    def organization_id(self):
        return getattr(self, "_organization_id", None) or (self.kitchen.organization_id if self.kitchen else "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    @organization_id.setter
    def organization_id(self, val):
        self._organization_id = val

    @property
    def season_or_cycle(self):
        return getattr(self, "_season_or_cycle", "SEASONAL_CYCLE")

    @season_or_cycle.setter
    def season_or_cycle(self, val):
        self._season_or_cycle = val

    @property
    def is_active(self):
        return getattr(self, "_is_active", True)

    @is_active.setter
    def is_active(self, val):
        self._is_active = val


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    menu_id = Column(String(36), ForeignKey("menus.id", ondelete="CASCADE"), nullable=False)
    dish_name = Column(String(255), nullable=False)
    planned_portions = Column(Integer, default=100, nullable=False)
    portion_weight_grams = Column(Float, default=400.0, nullable=False)
    dietary_category = Column(String(50), default="STANDARD", nullable=False)
    allergens = Column(JSON, default=list)
    cost_per_portion = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    menu = relationship("Menu", back_populates="items")

    def __init__(self, **kwargs):
        if "name" in kwargs and "dish_name" not in kwargs:
            kwargs["dish_name"] = kwargs.pop("name")
        if "serving_size_grams" in kwargs and "portion_weight_grams" not in kwargs:
            kwargs["portion_weight_grams"] = kwargs.pop("serving_size_grams")
        if "cost_per_serving_usd" in kwargs and "cost_per_portion" not in kwargs:
            kwargs["cost_per_portion"] = kwargs.pop("cost_per_serving_usd")
        elif "cost_per_portion_usd" in kwargs and "cost_per_portion" not in kwargs:
            kwargs["cost_per_portion"] = kwargs.pop("cost_per_portion_usd")
        if "category" in kwargs and "dietary_category" not in kwargs:
            kwargs["dietary_category"] = kwargs.pop("category")
        self._description = kwargs.pop("description", None)
        self._shelf_life = kwargs.pop("estimated_shelf_life_hours", 4.0)
        self._storage_temp = kwargs.pop("storage_temp_requirement", "HOT_HOLDING_60C")
        self._dietary_tags = kwargs.pop("dietary_tags", []) or kwargs.pop("dietary_flags", [])
        super().__init__(**kwargs)

    @property
    def name(self):
        return self.dish_name

    @name.setter
    def name(self, val):
        self.dish_name = val

    @property
    def category(self):
        return self.dietary_category

    @category.setter
    def category(self, val):
        self.dietary_category = val

    @property
    def serving_size_grams(self):
        return self.portion_weight_grams

    @serving_size_grams.setter
    def serving_size_grams(self, val):
        self.portion_weight_grams = val

    @property
    def cost_per_serving_usd(self):
        return self.cost_per_portion

    @cost_per_serving_usd.setter
    def cost_per_serving_usd(self, val):
        self.cost_per_portion = val

    @property
    def description(self):
        return getattr(self, "_description", None)

    @description.setter
    def description(self, val):
        self._description = val

    @property
    def estimated_shelf_life_hours(self):
        return getattr(self, "_shelf_life", 4.0)

    @estimated_shelf_life_hours.setter
    def estimated_shelf_life_hours(self, val):
        self._shelf_life = val

    @property
    def storage_temp_requirement(self):
        return getattr(self, "_storage_temp", "HOT_HOLDING_60C")

    @storage_temp_requirement.setter
    def storage_temp_requirement(self, val):
        self._storage_temp = val

    @property
    def dietary_tags(self):
        return getattr(self, "_dietary_tags", [])

    @dietary_tags.setter
    def dietary_tags(self, val):
        self._dietary_tags = val

    @property
    def is_active(self):
        return self.status == "ACTIVE"

    @is_active.setter
    def is_active(self, val):
        self.status = "ACTIVE" if val else "INACTIVE"



# ====================================================================
# 4. INVENTORY & PRODUCTION
# ====================================================================

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    unit = Column(String(50), default="kg", nullable=False)
    standard_cost_per_unit = Column(Float, default=0.0, nullable=False)
    allergen_profile = Column(JSON, default=list)
    storage_temp_category = Column(String(50), default="ROOM_TEMP", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    inventory_lots = relationship("Inventory", back_populates="ingredient", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        self._reorder_point = kwargs.pop("reorder_point", 10.0)
        self._supplier_name = kwargs.pop("supplier_name", "Primary Fresh Distributor")
        super().__init__(**kwargs)

    @property
    def reorder_point(self):
        return getattr(self, "_reorder_point", 10.0)

    @reorder_point.setter
    def reorder_point(self, val):
        self._reorder_point = val

    @property
    def supplier_name(self):
        return getattr(self, "_supplier_name", "Primary Fresh Distributor")

    @supplier_name.setter
    def supplier_name(self, val):
        self._supplier_name = val



class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    kitchen_id = Column(String(36), ForeignKey("kitchens.id", ondelete="CASCADE"), nullable=True)
    processing_unit_id = Column(String(36), ForeignKey("processing_units.id", ondelete="CASCADE"), nullable=True)
    ingredient_id = Column(String(36), ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False)
    lot_number = Column(String(100), nullable=False)
    current_quantity = Column(Float, nullable=False)
    reserved_quantity = Column(Float, default=0.0, nullable=False)
    unit = Column(String(50), default="kg", nullable=False)
    reorder_level = Column(Float, default=10.0, nullable=False)
    storage_temp = Column(String(50), default="ROOM_TEMP", nullable=False)
    storage_location = Column(String(100), default="Main Cold Room", nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="OPTIMAL", nullable=False)
    purchase_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    supplier = Column(String(255), nullable=True)
    cost_per_unit = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    kitchen = relationship("Kitchen", back_populates="inventory")
    processing_unit = relationship("ProcessingUnit", back_populates="inventory")
    ingredient = relationship("Ingredient", back_populates="inventory_lots")
    transactions = relationship("InventoryTransaction", back_populates="inventory", cascade="all, delete-orphan")

    # Compatibility properties
    @property
    def quantity(self):
        return self.current_quantity

    @quantity.setter
    def quantity(self, value):
        self.current_quantity = value

    @property
    def batch(self):
        return self.lot_number

    @batch.setter
    def batch(self, value):
        self.lot_number = value

    @property
    def batch_number(self):
        return self.lot_number

    @batch_number.setter
    def batch_number(self, value):
        self.lot_number = value

    @property
    def storage_type(self):
        return self.storage_temp

    @storage_type.setter
    def storage_type(self, value):
        self.storage_temp = value

    @property
    def storage_condition(self):
        return self.storage_temp

    @storage_condition.setter
    def storage_condition(self, value):
        self.storage_temp = value

    @property
    def cost(self):
        return self.cost_per_unit if self.cost_per_unit > 0 else (self.ingredient.standard_cost_per_unit if self.ingredient else 0.0)

    @cost.setter
    def cost(self, value):
        self.cost_per_unit = value

    @property
    def item_name(self):
        return self.ingredient.name if self.ingredient else "Stock Item"

    @property
    def category(self):
        return self.ingredient.category if self.ingredient else "PRODUCE"

    @property
    def is_quarantined(self):
        return self.status == "QUARANTINED"

    @property
    def organization_id(self):
        if self.ingredient:
            return self.ingredient.organization_id
        if self.kitchen:
            return self.kitchen.organization_id
        return "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    @organization_id.setter
    def organization_id(self, value):
        pass


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    inventory_id = Column(String(36), ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # INFLOW_PURCHASE, OUTFLOW_PREP, ADJUSTMENT, SURPLUS_DIVERTED, SPOILAGE_DISCARD
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    reference_id = Column(String(100), nullable=True)
    performed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    inventory = relationship("Inventory", back_populates="transactions")

    # Compatibility properties
    @property
    def quantity_change(self):
        return self.quantity

    @quantity_change.setter
    def quantity_change(self, value):
        self.quantity = value

    @property
    def resulting_balance(self):
        return self.inventory.current_quantity if self.inventory else 0.0


class ProductionBatch(Base):
    __tablename__ = "production_batches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    kitchen_id = Column(String(36), ForeignKey("kitchens.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(String(36), ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True)
    batch_number = Column(String(100), unique=True, nullable=False)
    planned_quantity = Column(Float, nullable=False)
    actual_prepared_quantity = Column(Float, default=0.0, nullable=False)
    unit = Column(String(50), default="portions", nullable=False)
    station = Column(String(100), nullable=False)
    target_temp_c = Column(Float, nullable=True)
    current_temp_c = Column(Float, nullable=True)
    haccp_compliant = Column(Boolean, default=True, nullable=False)
    chef_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="SCHEDULED", nullable=False)  # SCHEDULED, PREPPING, COOKING, HOLDING, COMPLETED, DISCARDED
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    kitchen = relationship("Kitchen", back_populates="batches")
    menu_item = relationship("MenuItem")
    consumption_records = relationship("ConsumptionRecord", back_populates="batch", cascade="all, delete-orphan")
    waste_records = relationship("WasteRecord", back_populates="batch")

    def __init__(self, **kwargs):
        self._organization_id = kwargs.pop("organization_id", None)
        if "planned_portions" in kwargs:
            kwargs["planned_quantity"] = float(kwargs.pop("planned_portions"))
        elif "planned_quantity" not in kwargs:
            kwargs["planned_quantity"] = 100.0

        if "actual_portions_prepped" in kwargs:
            kwargs["actual_prepared_quantity"] = float(kwargs.pop("actual_portions_prepped"))
        elif "actual_prepared_quantity" not in kwargs:
            kwargs["actual_prepared_quantity"] = kwargs.get("planned_quantity", 100.0)

        if "holding_temperature_c" in kwargs:
            kwargs["current_temp_c"] = float(kwargs.pop("holding_temperature_c"))
            kwargs["target_temp_c"] = kwargs["current_temp_c"]

        if "haccp_supervisor_user_id" in kwargs:
            kwargs["chef_user_id"] = kwargs.pop("haccp_supervisor_user_id")

        if "prep_start_time" in kwargs:
            kwargs["started_at"] = kwargs.pop("prep_start_time")
        if "prep_end_time" in kwargs:
            kwargs["completed_at"] = kwargs.pop("prep_end_time")
        if "production_date" in kwargs:
            self._production_date = kwargs.pop("production_date")
            if "started_at" not in kwargs or not kwargs["started_at"]:
                kwargs["started_at"] = self._production_date

        self._total_batch_weight_kg = kwargs.pop("total_batch_weight_kg", None)

        if "station" not in kwargs or not kwargs["station"]:
            kwargs["station"] = "Main Hot Prep Line"

        super().__init__(**kwargs)

    @property
    def organization_id(self):
        return getattr(self, "_organization_id", None) or (self.kitchen.organization_id if self.kitchen else "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    @organization_id.setter
    def organization_id(self, val):
        self._organization_id = val

    @property
    def planned_portions(self):
        return int(self.planned_quantity)

    @planned_portions.setter
    def planned_portions(self, val):
        self.planned_quantity = float(val)

    @property
    def actual_portions_prepped(self):
        return int(self.actual_prepared_quantity)

    @actual_portions_prepped.setter
    def actual_portions_prepped(self, val):
        self.actual_prepared_quantity = float(val)

    @property
    def total_batch_weight_kg(self):
        if getattr(self, "_total_batch_weight_kg", None):
            return self._total_batch_weight_kg
        return round(self.actual_prepared_quantity * 0.35 if self.actual_prepared_quantity > 0 else self.planned_quantity * 0.35, 2)

    @total_batch_weight_kg.setter
    def total_batch_weight_kg(self, val):
        self._total_batch_weight_kg = float(val)

    @property
    def holding_temperature_c(self):
        return self.current_temp_c if self.current_temp_c is not None else 65.0

    @holding_temperature_c.setter
    def holding_temperature_c(self, val):
        self.current_temp_c = float(val)

    @property
    def production_date(self):
        return getattr(self, "_production_date", None) or self.started_at or self.created_at

    @production_date.setter
    def production_date(self, val):
        self._production_date = val

    @property
    def prep_start_time(self):
        return self.started_at

    @prep_start_time.setter
    def prep_start_time(self, val):
        self.started_at = val

    @property
    def prep_end_time(self):
        return self.completed_at

    @prep_end_time.setter
    def prep_end_time(self, val):
        self.completed_at = val

    @property
    def haccp_supervisor_user_id(self):
        return self.chef_user_id

    @haccp_supervisor_user_id.setter
    def haccp_supervisor_user_id(self, val):
        self.chef_user_id = val


class ConsumptionRecord(Base):
    __tablename__ = "consumption_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    batch_id = Column(String(36), ForeignKey("production_batches.id", ondelete="CASCADE"), nullable=False)
    meal_service = Column(String(50), nullable=False)
    planned_headcount = Column(Integer, nullable=False)
    actual_headcount = Column(Integer, nullable=False)
    variance_percentage = Column(Float, default=0.0, nullable=False)
    total_prepared_kg = Column(Float, nullable=False)
    total_consumed_kg = Column(Float, nullable=False)
    unconsumed_kg = Column(Float, nullable=False)
    diverted_to_surplus_kg = Column(Float, default=0.0, nullable=False)
    recorded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    batch = relationship("ProductionBatch", back_populates="consumption_records")

    def __init__(self, **kwargs):
        self._organization_id = kwargs.pop("organization_id", None)
        self._kitchen_id = kwargs.pop("kitchen_id", None)
        if "production_batch_id" in kwargs and "batch_id" not in kwargs:
            kwargs["batch_id"] = kwargs.pop("production_batch_id")
        if "headcount_served" in kwargs:
            h = kwargs.pop("headcount_served")
            kwargs["actual_headcount"] = h
            if "planned_headcount" not in kwargs:
                kwargs["planned_headcount"] = h
        elif "actual_headcount" not in kwargs:
            kwargs["actual_headcount"] = 100
            kwargs["planned_headcount"] = 100

        if "portions_consumed" in kwargs:
            self._portions_consumed = kwargs.pop("portions_consumed")
            if "total_consumed_kg" not in kwargs:
                kwargs["total_consumed_kg"] = round(self._portions_consumed * 0.35, 2)
        elif "total_consumed_kg" not in kwargs:
            kwargs["total_consumed_kg"] = 35.0

        if "portions_remaining_surplus" in kwargs:
            self._portions_remaining_surplus = kwargs.pop("portions_remaining_surplus")

        if "surplus_weight_kg" in kwargs:
            self._surplus_weight_kg = kwargs.pop("surplus_weight_kg")
            if "unconsumed_kg" not in kwargs:
                kwargs["unconsumed_kg"] = self._surplus_weight_kg
        elif "unconsumed_kg" not in kwargs:
            kwargs["unconsumed_kg"] = 5.0

        if "total_prepared_kg" not in kwargs:
            kwargs["total_prepared_kg"] = round(kwargs["total_consumed_kg"] + kwargs["unconsumed_kg"], 2)

        super().__init__(**kwargs)

    @property
    def organization_id(self):
        return getattr(self, "_organization_id", None) or (self.batch.kitchen.organization_id if (self.batch and self.batch.kitchen) else "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    @organization_id.setter
    def organization_id(self, val):
        self._organization_id = val

    @property
    def kitchen_id(self):
        return getattr(self, "_kitchen_id", None) or (self.batch.kitchen_id if self.batch else None)

    @kitchen_id.setter
    def kitchen_id(self, val):
        self._kitchen_id = val

    @property
    def production_batch_id(self):
        return self.batch_id

    @production_batch_id.setter
    def production_batch_id(self, val):
        self.batch_id = val

    @property
    def headcount_served(self):
        return self.actual_headcount

    @headcount_served.setter
    def headcount_served(self, val):
        self.actual_headcount = val

    @property
    def portions_consumed(self):
        return getattr(self, "_portions_consumed", int(self.total_consumed_kg / 0.35) if self.total_consumed_kg else 0)

    @portions_consumed.setter
    def portions_consumed(self, val):
        self._portions_consumed = val

    @property
    def portions_remaining_surplus(self):
        return getattr(self, "_portions_remaining_surplus", int(self.unconsumed_kg / 0.35) if self.unconsumed_kg else 0)

    @portions_remaining_surplus.setter
    def portions_remaining_surplus(self, val):
        self._portions_remaining_surplus = val

    @property
    def surplus_weight_kg(self):
        return getattr(self, "_surplus_weight_kg", self.unconsumed_kg)

    @surplus_weight_kg.setter
    def surplus_weight_kg(self, val):
        self._surplus_weight_kg = val

    @property
    def service_date(self):
        return self.recorded_at

    @service_date.setter
    def service_date(self, val):
        self.recorded_at = val



class WasteRecord(Base):
    __tablename__ = "waste_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    kitchen_id = Column(String(36), ForeignKey("kitchens.id", ondelete="CASCADE"), nullable=False)
    batch_id = Column(String(36), ForeignKey("production_batches.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    food_item = Column(String(255), nullable=True)
    unit = Column(String(50), default="kg", nullable=False)
    notes = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    waste_category = Column(String(50), nullable=False)  # OVERPRODUCTION, PLATE_WASTE, SPOILAGE, EXPIRED, PREPARATION_WASTE, DAMAGED, QUALITY_REJECTION, OTHER
    weight_kg = Column(Float, nullable=False)
    cost_loss_usd = Column(Float, default=0.0, nullable=False)
    ghg_co2e_kg = Column(Float, default=0.0, nullable=False)
    epa_hierarchy_tier = Column(String(50), default="COMPOST", nullable=False)  # SOURCE_REDUCTION, FEED_HUNGRY_PEOPLE, FEED_ANIMALS, INDUSTRIAL_USES, COMPOST, LANDFILL
    department = Column(String(100), default="MAIN_KITCHEN", nullable=False)
    root_cause = Column(Text, nullable=True)
    logged_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    kitchen = relationship("Kitchen", back_populates="waste_records")
    batch = relationship("ProductionBatch", back_populates="waste_records")

    # Property aliases
    @property
    def category(self):
        return self.waste_category

    @category.setter
    def category(self, val):
        self.waste_category = val

    @property
    def quantity(self):
        return self.weight_kg

    @quantity.setter
    def quantity(self, val):
        self.weight_kg = val

    @property
    def quantity_kg(self):
        return self.weight_kg

    @quantity_kg.setter
    def quantity_kg(self, val):
        self.weight_kg = val

    @property
    def reason(self):
        return self.root_cause or self.waste_category

    @reason.setter
    def reason(self, val):
        self.root_cause = val

    @property
    def date(self):
        return self.recorded_at

    @date.setter
    def date(self, val):
        self.recorded_at = val

    @property
    def logged_at(self):
        return self.recorded_at

    @logged_at.setter
    def logged_at(self, val):
        self.recorded_at = val

    @property
    def production_batch(self):
        return self.batch_id

    @production_batch.setter
    def production_batch(self, val):
        self.batch_id = val

    @property
    def production_batch_id(self):
        return self.batch_id

    @production_batch_id.setter
    def production_batch_id(self, val):
        self.batch_id = val

    @property
    def financial_loss_usd(self):
        return self.cost_loss_usd

    @financial_loss_usd.setter
    def financial_loss_usd(self, val):
        self.cost_loss_usd = val

    @property
    def cost(self):
        return self.cost_loss_usd

    @cost.setter
    def cost(self, val):
        self.cost_loss_usd = val

    @property
    def epa_waste_tier(self):
        return self.epa_hierarchy_tier

    @epa_waste_tier.setter
    def epa_waste_tier(self, val):
        self.epa_hierarchy_tier = val

    @property
    def waste_cost(self):
        return self.cost_loss_usd

    @waste_cost.setter
    def waste_cost(self, val):
        self.cost_loss_usd = val

    @property
    def responsible_organization(self):
        return self.organization_id or (self.kitchen.organization_id if self.kitchen else "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    @responsible_organization.setter
    def responsible_organization(self, val):
        self.organization_id = val


    @property
    def corrective_action_taken(self):
        return None

    @corrective_action_taken.setter
    def corrective_action_taken(self, val):
        pass

    def __init__(self, **kwargs):
        # Map aliases
        if "category" in kwargs and "waste_category" not in kwargs:
            kwargs["waste_category"] = kwargs.pop("category")
        if "quantity" in kwargs and "weight_kg" not in kwargs:
            kwargs["weight_kg"] = kwargs.pop("quantity")
        if "quantity_kg" in kwargs and "weight_kg" not in kwargs:
            kwargs["weight_kg"] = kwargs.pop("quantity_kg")
        if "reason" in kwargs and "root_cause" not in kwargs:
            kwargs["root_cause"] = kwargs.pop("reason")
        if "date" in kwargs and "recorded_at" not in kwargs:
            kwargs["recorded_at"] = kwargs.pop("date")
        if "logged_at" in kwargs and "recorded_at" not in kwargs:
            kwargs["recorded_at"] = kwargs.pop("logged_at")
        if "production_batch" in kwargs and "batch_id" not in kwargs:
            kwargs["batch_id"] = kwargs.pop("production_batch")
        if "production_batch_id" in kwargs and "batch_id" not in kwargs:
            kwargs["batch_id"] = kwargs.pop("production_batch_id")
        if "cost" in kwargs and "cost_loss_usd" not in kwargs:
            kwargs["cost_loss_usd"] = kwargs.pop("cost")
        if "financial_loss_usd" in kwargs and "cost_loss_usd" not in kwargs:
            kwargs["cost_loss_usd"] = kwargs.pop("financial_loss_usd")
        if "epa_waste_tier" in kwargs and "epa_hierarchy_tier" not in kwargs:
            kwargs["epa_hierarchy_tier"] = kwargs.pop("epa_waste_tier")
        kwargs.pop("corrective_action_taken", None)
        super().__init__(**kwargs)


# ====================================================================
# 5. SURPLUS REDISTRIBUTION & LOGISTICS
# ====================================================================

class SurplusItem(Base):
    __tablename__ = "surplus_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    kitchen_id = Column(String(36), ForeignKey("kitchens.id", ondelete="SET NULL"), nullable=True)
    batch_id = Column(String(36), ForeignKey("production_batches.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, default="COOKED_MEALS")  # COOKED_MEALS, BAKERY, DAIRY, PRODUCE, PROTEIN, DRY_GOODS
    quantity_kg = Column(Float, nullable=False)
    portions = Column(Integer, nullable=False)
    storage_temp = Column(String(50), default="ROOM_TEMP", nullable=False)
    safe_consumption_deadline = Column(DateTime, nullable=True)
    blast_chilled_at = Column(DateTime, nullable=True)
    calculated_shelf_life_hours = Column(Float, default=4.0, nullable=False)
    urgency_tier = Column(String(50), default="STANDARD", nullable=False)  # STANDARD, EXPEDITED, CRITICAL_IMMEDIATE
    pickup_address = Column(Text, nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)
    dietary_tags = Column(JSON, default=list)
    status = Column(String(50), default="DECLARED", nullable=False)  # DECLARED, MATCHED, CLAIMED, IN_TRANSIT, DELIVERED, EXPIRED, DISCARDED
    packaging_type = Column(String(100), nullable=True)
    prepared_at = Column(DateTime, nullable=True)
    pickup_start = Column(DateTime, nullable=True)
    pickup_end = Column(DateTime, nullable=True)
    photo_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Phase 8 Real-Time Surplus & Food Safety Columns
    food = Column(String(255), nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String(50), default="kg", nullable=True)
    storage_type = Column(String(50), default="ROOM_TEMP", nullable=True)
    temperature = Column(Float, nullable=True)
    batch = Column(String(100), nullable=True)
    best_use_before = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    image = Column(Text, nullable=True)
    remaining_safe_window_minutes = Column(Float, nullable=True)
    urgency = Column(String(50), default="MEDIUM", nullable=True)
    eligibility = Column(String(50), default="ELIGIBLE_FOR_DONATION", nullable=True)
    required_action = Column(String(255), nullable=True)
    suggested_waste_workflow = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    approval_status = Column(String(50), default="APPROVED", nullable=True)
    approval_notes = Column(Text, nullable=True)
    location_name = Column(String(255), default="Main Production Kitchen", nullable=True)

    # Phase 9 Recipient Matching & Allocation Columns
    allocated_recipient_id = Column(String(36), ForeignKey("recipients.id", ondelete="SET NULL"), nullable=True)
    recipient_claim_status = Column(String(50), nullable=True)  # REQUESTED, ACCEPTED, REJECTED, PICKUP_SCHEDULED
    pickup_scheduled_time = Column(DateTime, nullable=True)
    pickup_driver_notes = Column(Text, nullable=True)

    # Phase 14 Food Processing Unit Traceability Link
    fpu_batch_id = Column(String(36), ForeignKey("fpu_production_batches.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="surplus_items")
    kitchen = relationship("Kitchen")
    donation_items = relationship("DonationItem", back_populates="surplus_item", cascade="all, delete-orphan")
    allocated_recipient = relationship("Recipient", foreign_keys=[allocated_recipient_id])
    fpu_batch = relationship("FpuProductionBatch", back_populates="surplus_items")

    # Compatibility alias properties
    @property
    def donor_id(self):
        return self.organization_id

    @donor_id.setter
    def donor_id(self, val):
        self.organization_id = val

    @property
    def expiry_at(self):
        return self.safe_consumption_deadline

    @expiry_at.setter
    def expiry_at(self, val):
        self.safe_consumption_deadline = val

    @property
    def estimated_shelf_life_hours(self):
        return self.calculated_shelf_life_hours

    @estimated_shelf_life_hours.setter
    def estimated_shelf_life_hours(self, val):
        self.calculated_shelf_life_hours = val

    @property
    def donor(self):
        return None

    @property
    def item_name(self):
        return self.title

    @item_name.setter
    def item_name(self, val):
        self.title = val

    @property
    def estimated_portions(self):
        return self.portions

    @estimated_portions.setter
    def estimated_portions(self, val):
        self.portions = val

    @property
    def storage_temp_condition(self):
        return self.storage_temp

    @storage_temp_condition.setter
    def storage_temp_condition(self, val):
        self.storage_temp = val

    @property
    def consumption_safe_until(self):
        return self.safe_consumption_deadline

    @consumption_safe_until.setter
    def consumption_safe_until(self, val):
        self.safe_consumption_deadline = val

    @property
    def pickup_window_start(self):
        return self.pickup_start

    @pickup_window_start.setter
    def pickup_window_start(self, val):
        self.pickup_start = val

    @property
    def pickup_window_end(self):
        return self.pickup_end

    @pickup_window_end.setter
    def pickup_window_end(self, val):
        self.pickup_end = val

    @property
    def production_batch_id(self):
        return self.batch_id

    @production_batch_id.setter
    def production_batch_id(self, val):
        self.batch_id = val

    @property
    def prepared_timestamp(self):
        return self.prepared_at

    @prepared_timestamp.setter
    def prepared_timestamp(self, val):
        self.prepared_at = val

    @property
    def haccp_verified(self):
        return True

    @haccp_verified.setter
    def haccp_verified(self, val):
        pass

    @property
    def allergens(self):
        return []

    @allergens.setter
    def allergens(self, val):
        pass

    def __init__(self, **kwargs):
        # Map known alias keys if present
        if "item_name" in kwargs and "title" not in kwargs:
            kwargs["title"] = kwargs.pop("item_name")
        if "estimated_portions" in kwargs and "portions" not in kwargs:
            kwargs["portions"] = kwargs.pop("estimated_portions")
        if "storage_temp_condition" in kwargs and "storage_temp" not in kwargs:
            kwargs["storage_temp"] = kwargs.pop("storage_temp_condition")
        if "consumption_safe_until" in kwargs and "safe_consumption_deadline" not in kwargs:
            kwargs["safe_consumption_deadline"] = kwargs.pop("consumption_safe_until")
        if "pickup_window_start" in kwargs and "pickup_start" not in kwargs:
            kwargs["pickup_start"] = kwargs.pop("pickup_window_start")
        if "pickup_window_end" in kwargs and "pickup_end" not in kwargs:
            kwargs["pickup_end"] = kwargs.pop("pickup_window_end")
        if "production_batch_id" in kwargs and "batch_id" not in kwargs:
            kwargs["batch_id"] = kwargs.pop("production_batch_id")
        if "prepared_timestamp" in kwargs and "prepared_at" not in kwargs:
            kwargs["prepared_at"] = kwargs.pop("prepared_timestamp")
        # Pop any virtual attributes that aren't DB columns
        kwargs.pop("haccp_verified", None)
        kwargs.pop("allergens", None)
        kwargs.pop("human_approval_required", None)
        super().__init__(**kwargs)


# Backward compatibility alias
FoodListing = SurplusItem


class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    facility_type = Column(String(50), nullable=False)  # FOOD_BANK, SOUP_KITCHEN, SHELTER, YOUTH_REFUGE, COMMUNITY_PANTRY
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    max_daily_intake_kg = Column(Float, default=200.0, nullable=False)
    cold_storage_available = Column(Boolean, default=True, nullable=False)
    walk_in_chiller_capacity_kg = Column(Float, default=50.0, nullable=False)
    verified_charity_id = Column(String(100), nullable=True)
    contact_person = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Phase 9 Recipient Data Fields
    pickup_available = Column(Boolean, default=True, nullable=True)
    current_demand_portions = Column(Integer, default=100, nullable=True)
    current_demand_kg = Column(Float, default=40.0, nullable=True)
    storage_capabilities = Column(JSON, default=lambda: ["COLD_HOLD", "DRY", "HOT_HOLD"], nullable=True)
    verification_status = Column(String(50), default="VERIFIED", nullable=True)  # VERIFIED, PENDING, UNVERIFIED
    reliability_score = Column(Float, default=0.96, nullable=True)  # 0.0 to 1.0 (96% reliability)
    operating_hours_description = Column(String(100), default="08:00 - 20:00 Daily", nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    requirements = relationship("RecipientRequirement", back_populates="recipient", uselist=False, cascade="all, delete-orphan")

    # Compatibility properties
    @property
    def recipient_type(self):
        return self.facility_type

    @recipient_type.setter
    def recipient_type(self, value):
        self.facility_type = value


class RecipientRequirement(Base):
    __tablename__ = "recipient_requirements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recipient_id = Column(String(36), ForeignKey("recipients.id", ondelete="CASCADE"), nullable=False)
    acceptable_categories = Column(JSON, default=list)
    dietary_preferences = Column(JSON, default=list)
    required_storage_temp = Column(String(50), default="ANY")
    min_portions_per_drop = Column(Integer, default=10, nullable=False)
    max_delivery_distance_km = Column(Float, default=25.0, nullable=False)
    operating_hours = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    recipient = relationship("Recipient", back_populates="requirements")


class Donation(Base):
    __tablename__ = "donations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    immutable_donation_id = Column(String(64), unique=True, index=True, nullable=True)
    donor_org_id = Column(String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    recipient_org_id = Column(String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=True)
    tracking_number = Column(String(100), unique=True, nullable=False)
    total_weight_kg = Column(Float, nullable=False)
    total_portions = Column(Integer, nullable=False)
    status = Column(String(50), default="DONATION_CREATED", nullable=False)  # DONATION_CREATED, ACCEPTED, PICKUP_ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, RECEIVED
    haccp_verified = Column(Boolean, default=True, nullable=False)
    declaration_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    safe_handling_ack = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    items = relationship("DonationItem", back_populates="donation", cascade="all, delete-orphan")
    pickup_requests = relationship("PickupRequest", back_populates="donation", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="donation", cascade="all, delete-orphan")
    custody_events = relationship("DonationCustodyEvent", back_populates="donation", cascade="all, delete-orphan", order_by="DonationCustodyEvent.timestamp")
    qr_tokens = relationship("DonationQrToken", back_populates="donation", cascade="all, delete-orphan")

    @property
    def pickup_request(self):
        return self.pickup_requests[0] if self.pickup_requests else None


class DonationItem(Base):
    __tablename__ = "donation_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    donation_id = Column(String(36), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False)
    surplus_item_id = Column(String(36), ForeignKey("surplus_items.id", ondelete="RESTRICT"), nullable=False)
    allocated_quantity_kg = Column(Float, nullable=False)
    allocated_portions = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    donation = relationship("Donation", back_populates="items")
    surplus_item = relationship("SurplusItem", back_populates="donation_items")


class PickupRequest(Base):
    __tablename__ = "pickup_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    donation_id = Column(String(36), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False)
    donor_address = Column(Text, nullable=False)
    donor_lat = Column(Float, nullable=False)
    donor_lng = Column(Float, nullable=False)
    ready_time = Column(DateTime, nullable=False)
    latest_pickup_time = Column(DateTime, nullable=False)
    assigned_driver_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, ACCEPTED, EN_ROUTE, COMPLETED, FAILED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    donation = relationship("Donation", back_populates="pickup_requests")


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    license_number = Column(String(100), unique=True, nullable=False)
    driver_status = Column(String(50), default="AVAILABLE", nullable=False)  # OFFLINE, AVAILABLE, EN_ROUTE_PICKUP, IN_TRANSIT, COMPLETED
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="driver_profile")
    organization = relationship("Organization", back_populates="drivers")
    vehicle = relationship("Vehicle", back_populates="driver")
    routes = relationship("Route", back_populates="driver")
    deliveries = relationship("Delivery", back_populates="driver")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    license_plate = Column(String(50), unique=True, nullable=False)
    vehicle_type = Column(String(50), default="STANDARD_VAN", nullable=False)  # REFRIGERATED_VAN, STANDARD_VAN, ELECTRIC_CARGO_VAN, HEAVY_TRUCK
    payload_capacity_kg = Column(Float, default=400.0, nullable=False)
    active_cooling = Column(Boolean, default=False, nullable=False)
    current_compartment_temp_c = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="vehicles")
    driver = relationship("Driver", back_populates="vehicle", uselist=False)


class Route(Base):
    __tablename__ = "routes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    driver_id = Column(String(36), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    route_code = Column(String(100), unique=True, nullable=False)
    total_distance_km = Column(Float, default=0.0, nullable=False)
    estimated_duration_mins = Column(Float, default=0.0, nullable=False)
    solver_status = Column(String(50), default="OPTIMAL", nullable=False)
    solver_model = Column(String(50), default="GOOGLE_OR_TOOLS_CVRPTW", nullable=False)
    waypoints_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="SCHEDULED", nullable=False)  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    driver = relationship("Driver", back_populates="routes")
    deliveries = relationship("Delivery", back_populates="route")


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="SET NULL"), nullable=True)
    donation_id = Column(String(36), ForeignKey("donations.id", ondelete="CASCADE"), nullable=True)
    surplus_item_id = Column(String(36), ForeignKey("surplus_items.id", ondelete="SET NULL"), nullable=True)
    pickup_request_id = Column(String(36), ForeignKey("pickup_requests.id", ondelete="SET NULL"), nullable=True)
    driver_id = Column(String(36), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)

    # Waypoints & Addresses
    pickup_address = Column(Text, nullable=True)
    pickup_lat = Column(Float, nullable=True)
    pickup_lng = Column(Float, nullable=True)
    delivery_address = Column(Text, nullable=True)
    delivery_lat = Column(Float, nullable=True)
    delivery_lng = Column(Float, nullable=True)

    # Cargo Details & Timing
    food_title = Column(String(255), nullable=True)
    food_urgency = Column(String(50), default="MEDIUM", nullable=True)
    cargo_weight_kg = Column(Float, default=15.0, nullable=True)
    scheduled_pickup_time = Column(DateTime, nullable=True)
    scheduled_delivery_time = Column(DateTime, nullable=True)
    estimated_arrival_time = Column(DateTime, nullable=True)  # Real-time / computed ETA

    stop_sequence = Column(Integer, default=1, nullable=False)
    # Statuses: ASSIGNED, EN_ROUTE, ARRIVED, PICKED_UP, IN_TRANSIT, DELIVERED, FAILED, CANCELLED
    status = Column(String(50), default="ASSIGNED", nullable=False)
    departure_at = Column(DateTime, nullable=True)
    arrival_at = Column(DateTime, nullable=True)
    actual_temp_at_delivery_c = Column(Float, nullable=True)
    distance_km = Column(Float, default=0.0, nullable=False)
    transit_time_mins = Column(Float, default=0.0, nullable=False)

    # Proof of Delivery
    proof_of_delivery_signature = Column(Text, nullable=True)
    proof_of_delivery_photo = Column(Text, nullable=True)
    proof_of_delivery_notes = Column(Text, nullable=True)
    proof_of_delivery_receiver_name = Column(String(255), nullable=True)
    proof_of_delivery_verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    route = relationship("Route", back_populates="deliveries")
    donation = relationship("Donation", back_populates="deliveries")
    driver = relationship("Driver", back_populates="deliveries")
    vehicle = relationship("Vehicle")
    surplus_item = relationship("SurplusItem")
    qr_verifications = relationship("QrVerification", back_populates="delivery", cascade="all, delete-orphan")


# Backward compatibility alias
class RescueClaim:
    """Mock alias adapter for backward compatibility with phase 0 tests."""
    pass


class QrVerification(Base):
    __tablename__ = "qr_verifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    delivery_id = Column(String(36), ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(50), nullable=False)  # PICKUP_HANDOVER, DELIVERY_RECEIPT
    nonce = Column(String(64), unique=True, nullable=False)
    hmac_signature = Column(String(128), nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_burned = Column(Boolean, default=False, nullable=False)
    burned_at = Column(DateTime, nullable=True)
    verified_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_lat = Column(Float, nullable=True)
    verified_lng = Column(Float, nullable=True)
    verified_temp_c = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    delivery = relationship("Delivery", back_populates="qr_verifications")


class DonationCustodyEvent(Base):
    __tablename__ = "donation_custody_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    donation_id = Column(String(36), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False)
    event = Column(String(100), nullable=False)  # KITCHEN_HANDOVER, DRIVER_PICKUP, IN_TRANSIT_DEPARTURE, COURIER_DELIVERY, RECIPIENT_RECEIPT, DONATION_CREATED, DONATION_ACCEPTED, PICKUP_ASSIGNED
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    user_id = Column(String(36), nullable=True)
    user_name = Column(String(150), nullable=True)
    role = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    token_nonce = Column(String(64), nullable=True)
    proof_type = Column(String(50), nullable=True)  # SIGNATURE, TEMPERATURE_READING, PHOTO, SEAL_CHECK, GPS_PIN
    verified_temp_c = Column(Float, nullable=True)
    verified_lat = Column(Float, nullable=True)
    verified_lng = Column(Float, nullable=True)
    signature_data = Column(Text, nullable=True)
    proof_image_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    proof_metadata = Column(JSON, default=dict, nullable=True)
    previous_hash = Column(String(64), nullable=True)
    integrity_hash = Column(String(64), nullable=False)

    # Relationships
    donation = relationship("Donation", back_populates="custody_events")


class DonationQrToken(Base):
    __tablename__ = "donation_qr_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    donation_id = Column(String(36), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(50), nullable=False)  # KITCHEN_HANDOVER, DRIVER_PICKUP, RECIPIENT_RECEIPT
    nonce = Column(String(64), unique=True, nullable=False)
    hmac_signature = Column(String(128), nullable=False)
    token_string = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_burned = Column(Boolean, default=False, nullable=False)
    burned_at = Column(DateTime, nullable=True)
    burned_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    donation = relationship("Donation", back_populates="qr_tokens")



# ====================================================================
# 6. INTELLIGENCE, GOVERNANCE & AUDIT
# ====================================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # URGENT_EXPIRY, DISPATCH, PRODUCTION, AUDIT, SYSTEM
    priority = Column(String(50), default="NORMAL", nullable=False)  # LOW, NORMAL, HIGH, CRITICAL
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    action_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")
    organization = relationship("Organization")


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    kitchen_id = Column(String(36), ForeignKey("kitchens.id", ondelete="SET NULL"), nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), default="v1.0", nullable=False)
    prediction_type = Column(String(50), nullable=False)  # DEMAND_HEADCOUNT, SURPLUS_QUANTITY_KG, SPOILAGE_RISK
    target_date = Column(DateTime, nullable=False)
    predicted_value = Column(Float, nullable=False)
    confidence_lower_bound = Column(Float, nullable=True)
    confidence_upper_bound = Column(Float, nullable=True)
    features_payload = Column(JSON, default=dict, nullable=False)
    r2_score = Column(Float, default=0.829, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization = relationship("Organization")


class AiRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    prediction_id = Column(String(36), ForeignKey("model_predictions.id", ondelete="SET NULL"), nullable=True)
    recipe_or_item_name = Column(String(255), nullable=False)
    recommendation_type = Column(String(50), nullable=False)  # BATCH_SIZE_ADJUSTMENT, SURPLUS_DIVERSION, EXPIRATION_PRIORITY
    recommended_action = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    estimated_waste_reduction_kg = Column(Float, default=0.0, nullable=False)
    estimated_cost_savings_usd = Column(Float, default=0.0, nullable=False)
    confidence_percentage = Column(Integer, nullable=False)
    is_applied = Column(Boolean, default=False, nullable=False)
    applied_at = Column(DateTime, nullable=True)
    applied_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization = relationship("Organization")
    prediction = relationship("ModelPrediction")


class ImpactMetric(Base):
    __tablename__ = "impact_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    donation_id = Column(String(36), ForeignKey("donations.id", ondelete="SET NULL"), nullable=True)
    waste_record_id = Column(String(36), ForeignKey("waste_records.id", ondelete="SET NULL"), nullable=True)
    food_diverted_kg = Column(Float, default=0.0, nullable=False)
    meals_provided = Column(Integer, default=0, nullable=False)
    co2e_avoided_kg = Column(Float, default=0.0, nullable=False)
    water_saved_liters = Column(Float, default=0.0, nullable=False)
    financial_value_usd = Column(Float, default=0.0, nullable=False)
    calculation_methodology = Column(String(100), default="EPA_WARM_V15", nullable=False)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization = relationship("Organization")

    # Compatibility properties
    @property
    def co2_kg_saved(self):
        return self.co2e_avoided_kg

    @property
    def water_liters_saved(self):
        return self.water_saved_liters


class ImpactEmissionFactor(Base):
    __tablename__ = "impact_emission_factors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)  # NULL = global default benchmark
    category = Column(String(50), default="DEFAULT", nullable=False)  # PRODUCE, DAIRY, MEAT_POULTRY, BAKERY, PREPARED_MEALS, SEAFOOD, GRAINS_DRY, DEFAULT
    co2e_kg_per_kg_food = Column(Float, default=2.5, nullable=False)  # EPA WARM baseline default 2.5 kg CO2e / kg food
    water_liters_per_kg_food = Column(Float, default=1850.0, nullable=False)  # Average agricultural lifecycle water footprint
    landfill_diversion_m3_per_kg = Column(Float, default=0.0015, nullable=False)  # Landfill compaction factor
    meal_equivalent_kg = Column(Float, default=0.42, nullable=False)  # USDA / Feeding America standard meal portion (approx 0.42 kg)
    people_served_per_meal = Column(Float, default=1.0, nullable=False)
    economic_value_usd_per_kg = Column(Float, default=5.50, nullable=False)  # Average retail value of rescued food ($5.50/kg)
    production_cost_factor_per_kg = Column(Float, default=3.25, nullable=False)  # Avoided cost of re-procurement / labor
    documentation_source = Column(String(255), default="EPA WARM v15 (2023) / FAO Food Wastage Footprint / Feeding America Standard", nullable=False)
    is_estimate = Column(Boolean, default=True, nullable=False)  # Explicitly labeled as estimate
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization = relationship("Organization")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # FDA_FOOD_CODE, GOOD_SAMARITAN_ACT, HACCP_SOP, COLD_CHAIN_STANDARD, MUNICIPAL_BYLAW
    document_type = Column(String(100), nullable=True)  # HACCP_SOP, INSTITUTIONAL_POLICY, WASTE_MANAGEMENT_POLICY, DONATION_PROCEDURE, GOVERNMENT_GUIDELINE, OPERATIONAL_MANUAL
    content = Column(Text, nullable=False)
    regulatory_source = Column(String(255), nullable=True)
    document_version = Column(String(50), default="2024.1", nullable=True)
    access_level = Column(String(50), default="PUBLIC", nullable=False)  # PUBLIC, ORGANIZATION_INTERNAL, CONFIDENTIAL, ADMIN_ONLY
    doc_date = Column(Date, nullable=True)
    embedding_vector = Column(JSON, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_index")
    organization = relationship("Organization")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    chunk_metadata = Column(JSON, default=dict, nullable=False)
    embedding_vector = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    organization = relationship("Organization")


class RagChatMessage(Base):
    __tablename__ = "rag_chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), nullable=True)
    organization_id = Column(String(36), nullable=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list, nullable=False)
    data_context = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


# Backward compatibility alias
KnowledgeDoc = Document


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    module = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    entity_name = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    sha256_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class VisionScan(Base):
    __tablename__ = "vision_scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    kitchen_id = Column(String(36), ForeignKey("kitchens.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    image_url = Column(Text, nullable=False)
    prediction = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    confidence_tier = Column(String(20), nullable=False)  # HIGH, MODERATE, LOW
    requires_manual_confirmation = Column(Boolean, default=True, nullable=False)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    corrected_label = Column(String(50), nullable=True)
    detected_bounding_box = Column(JSON, default=dict, nullable=False)
    top_candidates = Column(JSON, default=list, nullable=False)
    preprocessing_metadata = Column(JSON, default=dict, nullable=False)
    created_record_type = Column(String(50), nullable=True)  # WASTE_RECORD, SURPLUS_ITEM
    created_record_id = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization")
    kitchen = relationship("Kitchen")
    user = relationship("User")


class SystemBusinessRule(Base):
    __tablename__ = "system_business_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_key = Column(String(100), unique=True, nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    category = Column(String(50), default="OPERATIONS", nullable=False)  # OPERATIONS, FOOD_SAFETY, ML_FORECAST, LOGISTICS, NOTIFICATIONS
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    updated_by = relationship("User")
