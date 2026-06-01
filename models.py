"""中药诊疗管理系统 — 数据模型"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Herb:
    id: Optional[int] = None
    name: str = ""
    alias: str = ""
    supplier: str = ""
    purchase_price: float = 0.0
    sell_price: float = 0.0
    purchase_date: str = ""
    shelf_life_days: int = 365
    expiry_date: str = ""
    stock_qty: float = 0.0
    stock_warn_threshold: float = 5.0
    expiry_warn_days: int = 30
    purchase_note: str = ""
    name2: str = ""
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def from_row(row):
        return Herb(
            id=row["id"], name=row["name"], alias=row["alias"] or "",
            supplier=row["supplier"] or "", purchase_price=row["purchase_price"] or 0,
            sell_price=row["sell_price"] or 0, purchase_date=row["purchase_date"] or "",
            shelf_life_days=row["shelf_life_days"] or 365,
            expiry_date=row["expiry_date"] or "", stock_qty=row["stock_qty"] or 0,
            stock_warn_threshold=row["stock_warn_threshold"] or 5,
            expiry_warn_days=row["expiry_warn_days"] or 30,
            purchase_note=row["purchase_note"] or "",
            name2=row["name2"] or "",
            created_at=row["created_at"] or "", updated_at=row["updated_at"] or ""
        )


@dataclass
class Patient:
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    age: int = 0
    gender: str = ""
    occupation: str = ""
    address: str = ""
    condition: str = ""
    monthly_no: str = ""
    medical_record_no: str = ""
    visit_date: str = ""
    diagnosis: str = ""
    treatment: str = ""
    created_at: str = ""

    @staticmethod
    def from_row(row):
        return Patient(
            id=row["id"], name=row["name"], phone=row["phone"] or "",
            age=row["age"] or 0, gender=row["gender"] or "",
            occupation=row["occupation"] or "",
            address=row["address"] or "", condition=row["condition"] or "",
            monthly_no=row["monthly_no"] or "",
            medical_record_no=row["medical_record_no"] or "",
            visit_date=row["visit_date"] or "",
            diagnosis=row["diagnosis"] or "",
            treatment=row["treatment"] or "",
            created_at=row["created_at"] or "",
        )


@dataclass
class Formula:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    category: str = ""
    is_builtin: bool = True
    items: list = field(default_factory=list)

    @staticmethod
    def from_row(row):
        return Formula(
            id=row["id"], name=row["name"], description=row["description"] or "",
            category=row["category"] or "", is_builtin=bool(row["is_builtin"]),
        )


@dataclass
class FormulaItem:
    id: Optional[int] = None
    formula_id: int = 0
    herb_id: int = 0
    herb_name: str = ""
    default_grams: float = 9.0


@dataclass
class Prescription:
    id: Optional[int] = None
    prescription_no: str = ""
    patient_id: int = 0
    patient_name: str = ""
    formula_name: str = ""
    diagnosis: str = ""
    treatment: str = ""
    total_price: float = 0.0
    items: list = field(default_factory=list)
    created_at: str = ""

    @staticmethod
    def from_row(row):
        return Prescription(
            id=row["id"], prescription_no=row["prescription_no"],
            patient_id=row["patient_id"] or 0,
            formula_name=row["formula_name"] or "",
            diagnosis=row["diagnosis"] or "",
            treatment=row["treatment"] or "",
            total_price=row["total_price"] or 0,
            created_at=row["created_at"] or "",
        )


@dataclass
class PrescriptionItem:
    id: Optional[int] = None
    prescription_id: int = 0
    herb_id: int = 0
    herb_name: str = ""
    actual_grams: float = 0.0
    unit_price: float = 0.0


@dataclass
class StockInRecord:
    id: Optional[int] = None
    herb_id: int = 0
    herb_name: str = ""
    supplier: str = ""
    qty: float = 0.0
    purchase_price: float = 0.0
    purchase_date: str = ""
    shelf_life_days: int = 365
    expiry_date: str = ""
    approver: str = ""
    status: str = "pending"
    created_at: str = ""

    @staticmethod
    def from_row(row):
        return StockInRecord(
            id=row["id"], herb_id=row["herb_id"],
            herb_name=row["herb_name"] or "",
            supplier=row["supplier"] or "",
            qty=row["qty"] or 0, purchase_price=row["purchase_price"] or 0,
            purchase_date=row["purchase_date"] or "",
            shelf_life_days=row["shelf_life_days"] or 365,
            expiry_date=row["expiry_date"] or "",
            approver=row["approver"] or "",
            status=row["status"] or "pending",
            created_at=row["created_at"] or "",
        )
