# models/drug_models.py

from typing import Optional, Dict, Any
from datetime import datetime

class Drug:
    """مدل دارو"""
    
    def __init__(
        self,
        id: Optional[int] = None,
        generic_name: str = '',
        en_brand_name: str = '',
        generic_code: str = '',
        form: str = '',
        dosage: str = '',
        price_per_unit: int = 0,
        stock: int = 0,
        min_stock_alert_level: int = 0,
        barcode: str = '',
        qr_code: str = '',
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.id = id
        self.generic_name = generic_name
        self.en_brand_name = en_brand_name
        self.generic_code = generic_code
        self.form = form
        self.dosage = dosage
        self.price_per_unit = price_per_unit
        self.stock = stock
        self.min_stock_alert_level = min_stock_alert_level
        self.barcode = barcode
        self.qr_code = qr_code
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return {
            'id': self.id,
            'generic_name': self.generic_name,
            'en_brand_name': self.en_brand_name,
            'generic_code': self.generic_code,
            'form': self.form,
            'dosage': self.dosage,
            'price_per_unit': self.price_per_unit,
            'stock': self.stock,
            'min_stock_alert_level': self.min_stock_alert_level,
            'barcode': self.barcode,
            'qr_code': self.qr_code,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Drug':
        """ایجاد از dictionary"""
        return cls(**data)
    
    @classmethod
    def from_db_row(cls, row) -> 'Drug':
        """ایجاد از row دیتابیس"""
        return cls(
            id=row['id'] if 'id' in row.keys() else None,
            generic_name=row['generic_name'] if 'generic_name' in row.keys() else '',
            en_brand_name=row['en_brand_name'] if 'en_brand_name' in row.keys() else '',
            generic_code=row['generic_code'] if 'generic_code' in row.keys() else '',
            form=row['form'] if 'form' in row.keys() else '',
            dosage=row['dosage'] if 'dosage' in row.keys() else '',
            price_per_unit=row['price_per_unit'] if 'price_per_unit' in row.keys() else 0,
            stock=row['stock'] if 'stock' in row.keys() else 0,
            min_stock_alert_level=row['min_stock_alert_level'] if 'min_stock_alert_level' in row.keys() else 0,
            barcode=row['barcode'] if 'barcode' in row.keys() else '',
            qr_code=row['qr_code'] if 'qr_code' in row.keys() else '',
            created_at=row['created_at'] if 'created_at' in row.keys() else None,
            updated_at=row['updated_at'] if 'updated_at' in row.keys() else None
        )
    
    def is_low_stock(self) -> bool:
        """بررسی کم بودن موجودی"""
        return self.stock <= self.min_stock_alert_level and self.min_stock_alert_level > 0
    
    def is_out_of_stock(self) -> bool:
        """بررسی تمام شدن موجودی"""
        return self.stock <= 0
    
    def calculate_stock_status(self) -> str:
        """محاسبه وضعیت موجودی"""
        if self.is_out_of_stock():
            return "ناموجود"
        elif self.is_low_stock():
            return "کم موجود"
        else:
            return "موجود"
    
    def __str__(self) -> str:
        return f"{self.generic_name} ({self.generic_code})"
    
    def __repr__(self) -> str:
        return f"Drug(id={self.id}, generic_name='{self.generic_name}', stock={self.stock})"


class Prescription:
    """مدل نسخه"""
    
    def __init__(
        self,
        id: Optional[int] = None,
        prescription_number: str = '',
        sale_type: str = '',
        date: str = '',
        total_price: int = 0,
        insurance_name: str = '',
        version_type: str = '',
        serial_number: str = '',
        patient_first_name: str = '',
        patient_last_name: str = '',
        patient_national_code: str = '',
        patient_phone_number: str = '',
        patient_birth_date: str = '',
        doctor_id: Optional[int] = None,
        created_at: Optional[str] = None
    ):
        self.id = id
        self.prescription_number = prescription_number
        self.sale_type = sale_type
        self.date = date
        self.total_price = total_price
        self.insurance_name = insurance_name
        self.version_type = version_type
        self.serial_number = serial_number
        self.patient_first_name = patient_first_name
        self.patient_last_name = patient_last_name
        self.patient_national_code = patient_national_code
        self.patient_phone_number = patient_phone_number
        self.patient_birth_date = patient_birth_date
        self.doctor_id = doctor_id
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return {
            'id': self.id,
            'prescription_number': self.prescription_number,
            'sale_type': self.sale_type,
            'date': self.date,
            'total_price': self.total_price,
            'insurance_name': self.insurance_name,
            'version_type': self.version_type,
            'serial_number': self.serial_number,
            'patient_first_name': self.patient_first_name,
            'patient_last_name': self.patient_last_name,
            'patient_national_code': self.patient_national_code,
            'patient_phone_number': self.patient_phone_number,
            'patient_birth_date': self.patient_birth_date,
            'doctor_id': self.doctor_id,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_db_row(cls, row) -> 'Prescription':
        """ایجاد از row دیتابیس"""
        return cls(
            id=row['id'] if 'id' in row.keys() else None,
            prescription_number=row['prescription_number'] if 'prescription_number' in row.keys() else '',
            sale_type=row['sale_type'] if 'sale_type' in row.keys() else '',
            date=row['date'] if 'date' in row.keys() else '',
            total_price=row['total_price'] if 'total_price' in row.keys() else 0,
            insurance_name=row['insurance_name'] if 'insurance_name' in row.keys() else '',
            version_type=row['version_type'] if 'version_type' in row.keys() else '',
            serial_number=row['serial_number'] if 'serial_number' in row.keys() else '',
            patient_first_name=row['patient_first_name'] if 'patient_first_name' in row.keys() else '',
            patient_last_name=row['patient_last_name'] if 'patient_last_name' in row.keys() else '',
            patient_national_code=row['patient_national_code'] if 'patient_national_code' in row.keys() else '',
            patient_phone_number=row['patient_phone_number'] if 'patient_phone_number' in row.keys() else '',
            patient_birth_date=row['patient_birth_date'] if 'patient_birth_date' in row.keys() else '',
            doctor_id=row['doctor_id'] if 'doctor_id' in row.keys() else None,
            created_at=row['created_at'] if 'created_at' in row.keys() else None
        )
    
    def get_patient_full_name(self) -> str:
        """دریافت نام کامل بیمار"""
        return f"{self.patient_first_name} {self.patient_last_name}".strip()
    
    def get_display_title(self) -> str:
        """دریافت عنوان نمایشی نسخه"""
        patient_name = self.get_patient_full_name()
        if patient_name:
            return f"نسخه {self.prescription_number} - {patient_name}"
        return f"نسخه {self.prescription_number}"
    
    def __str__(self) -> str:
        return self.get_display_title()
    
    def __repr__(self) -> str:
        return f"Prescription(id={self.id}, number='{self.prescription_number}', patient='{self.get_patient_full_name()}')"


class PrescriptionItem:
    """مدل آیتم نسخه"""
    
    def __init__(
        self,
        id: Optional[int] = None,
        prescription_id: int = 0,
        drug_name: str = '',
        dosage: str = '',
        form: str = '',
        generic_code: str = '',
        packaging: str = '',
        insurance: int = 0,
        unit_price: int = 0,
        quantity: int = 0,
        total_price: int = 0,
        usage_instructions: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        self.id = id
        self.prescription_id = prescription_id
        self.drug_name = drug_name
        self.dosage = dosage
        self.form = form
        self.generic_code = generic_code
        self.packaging = packaging
        self.insurance = insurance
        self.unit_price = unit_price
        self.quantity = quantity
        self.total_price = total_price
        self.usage_instructions = usage_instructions
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return {
            'id': self.id,
            'prescription_id': self.prescription_id,
            'drug_name': self.drug_name,
            'dosage': self.dosage,
            'form': self.form,
            'generic_code': self.generic_code,
            'packaging': self.packaging,
            'insurance': self.insurance,
            'unit_price': self.unit_price,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'usage_instructions': self.usage_instructions,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_db_row(cls, row) -> 'PrescriptionItem':
        """ایجاد از row دیتابیس"""
        return cls(
            id=row['id'] if 'id' in row.keys() else None,
            prescription_id=row['prescription_id'] if 'prescription_id' in row.keys() else 0,
            drug_name=row['drug_name'] if 'drug_name' in row.keys() else '',
            dosage=row['dosage'] if 'dosage' in row.keys() else '',
            form=row['form'] if 'form' in row.keys() else '',
            generic_code=row['generic_code'] if 'generic_code' in row.keys() else '',
            packaging=row['packaging'] if 'packaging' in row.keys() else '',
            insurance=row['insurance'] if 'insurance' in row.keys() else 0,
            unit_price=row['unit_price'] if 'unit_price' in row.keys() else 0,
            quantity=row['quantity'] if 'quantity' in row.keys() else 0,
            total_price=row['total_price'] if 'total_price' in row.keys() else 0,
            usage_instructions=row['usage_instructions'] if 'usage_instructions' in row.keys() else None,
            created_at=row['created_at'] if 'created_at' in row.keys() else None
        )
    
    def calculate_item_total(self) -> int:
        """محاسبه مجموع قیمت آیتم"""
        return self.unit_price * self.quantity
    
    def get_display_name(self) -> str:
        """نام نمایشی آیتم"""
        if self.dosage and self.form:
            return f"{self.drug_name} {self.dosage} ({self.form})"
        elif self.dosage:
            return f"{self.drug_name} {self.dosage}"
        return self.drug_name
    
    def __str__(self) -> str:
        return f"{self.get_display_name()} x{self.quantity}"
    
    def __repr__(self) -> str:
        return f"PrescriptionItem(id={self.id}, drug='{self.drug_name}', quantity={self.quantity})"


class Doctor:
    """مدل دکتر"""
    
    def __init__(
        self,
        id: Optional[int] = None,
        first_name: str = '',
        last_name: str = '',
        medical_council_id: str = '',
        phone_number: str = '',
        specialty: str = '',
        created_at: Optional[str] = None
    ):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.medical_council_id = medical_council_id
        self.phone_number = phone_number
        self.specialty = specialty
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'medical_council_id': self.medical_council_id,
            'phone_number': self.phone_number,
            'specialty': self.specialty,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_db_row(cls, row) -> 'Doctor':
        """ایجاد از row دیتابیس"""
        return cls(
            id=row['id'] if 'id' in row.keys() else None,
            first_name=row['first_name'] if 'first_name' in row.keys() else '',
            last_name=row['last_name'] if 'last_name' in row.keys() else '',
            medical_council_id=row['medical_council_id'] if 'medical_council_id' in row.keys() else '',
            phone_number=row['phone_number'] if 'phone_number' in row.keys() else '',
            specialty=row['specialty'] if 'specialty' in row.keys() else '',
            created_at=row['created_at'] if 'created_at' in row.keys() else None
        )
    
    def get_full_name(self) -> str:
        """دریافت نام کامل دکتر"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"دکتر {full_name}" if full_name else "دکتر"
    
    def get_display_info(self) -> str:
        """اطلاعات نمایشی کامل دکتر"""
        full_name = self.get_full_name()
        if self.medical_council_id:
            full_name += f" (کد نظام: {self.medical_council_id})"
        if self.specialty:
            full_name += f" - {self.specialty}"
        return full_name
    
    def __str__(self) -> str:
        return self.get_display_info()
    
    def __repr__(self) -> str:
        return f"Doctor(id={self.id}, name='{self.get_full_name()}', council_id='{self.medical_council_id}')"


class CompanyPurchase:
    """مدل خرید شرکت"""
    
    def __init__(
        self,
        id: Optional[int] = None,
        document_row_number: str = '',
        registration_date: str = '',
        document_type: str = '',
        supplier_name: str = '',
        description: str = '',
        apply_to_shelf_directly: int = 0,
        invoice_type: str = '',
        invoice_number: str = '',
        invoice_date: str = '',
        settlement_period_days: int = 0,
        settlement_date: str = '',
        total_items_purchase_price: float = 0.0,
        total_items_sale_price: float = 0.0,
        overall_document_discount: float = 0.0,
        document_product_discount: float = 0.0,
        document_tax_levies: float = 0.0,
        items_tax_levies: float = 0.0,
        shipping_cost: float = 0.0,
        payable_amount: float = 0.0,
        created_at: Optional[str] = None
    ):
        self.id = id
        self.document_row_number = document_row_number
        self.registration_date = registration_date
        self.document_type = document_type
        self.supplier_name = supplier_name
        self.description = description
        self.apply_to_shelf_directly = apply_to_shelf_directly
        self.invoice_type = invoice_type
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        self.settlement_period_days = settlement_period_days
        self.settlement_date = settlement_date
        self.total_items_purchase_price = total_items_purchase_price
        self.total_items_sale_price = total_items_sale_price
        self.overall_document_discount = overall_document_discount
        self.document_product_discount = document_product_discount
        self.document_tax_levies = document_tax_levies
        self.items_tax_levies = items_tax_levies
        self.shipping_cost = shipping_cost
        self.payable_amount = payable_amount
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return {
            'id': self.id,
            'document_row_number': self.document_row_number,
            'registration_date': self.registration_date,
            'document_type': self.document_type,
            'supplier_name': self.supplier_name,
            'description': self.description,
            'apply_to_shelf_directly': self.apply_to_shelf_directly,
            'invoice_type': self.invoice_type,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date,
            'settlement_period_days': self.settlement_period_days,
            'settlement_date': self.settlement_date,
            'total_items_purchase_price': self.total_items_purchase_price,
            'total_items_sale_price': self.total_items_sale_price,
            'overall_document_discount': self.overall_document_discount,
            'document_product_discount': self.document_product_discount,
            'document_tax_levies': self.document_tax_levies,
            'items_tax_levies': self.items_tax_levies,
            'shipping_cost': self.shipping_cost,
            'payable_amount': self.payable_amount,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_db_row(cls, row) -> 'CompanyPurchase':
        """ایجاد از row دیتابیس"""
        return cls(
            id=row['id'] if 'id' in row.keys() else None,
            document_row_number=row['document_row_number'] if 'document_row_number' in row.keys() else '',
            registration_date=row['registration_date'] if 'registration_date' in row.keys() else '',
            document_type=row['document_type'] if 'document_type' in row.keys() else '',
            supplier_name=row['supplier_name'] if 'supplier_name' in row.keys() else '',
            description=row['description'] if 'description' in row.keys() else '',
            apply_to_shelf_directly=row['apply_to_shelf_directly'] if 'apply_to_shelf_directly' in row.keys() else 0,
            invoice_type=row['invoice_type'] if 'invoice_type' in row.keys() else '',
            invoice_number=row['invoice_number'] if 'invoice_number' in row.keys() else '',
            invoice_date=row['invoice_date'] if 'invoice_date' in row.keys() else '',
            settlement_period_days=row['settlement_period_days'] if 'settlement_period_days' in row.keys() else 0,
            settlement_date=row['settlement_date'] if 'settlement_date' in row.keys() else '',
            total_items_purchase_price=row['total_items_purchase_price'] if 'total_items_purchase_price' in row.keys() else 0.0,
            total_items_sale_price=row['total_items_sale_price'] if 'total_items_sale_price' in row.keys() else 0.0,
            overall_document_discount=row['overall_document_discount'] if 'overall_document_discount' in row.keys() else 0.0,
            document_product_discount=row['document_product_discount'] if 'document_product_discount' in row.keys() else 0.0,
            document_tax_levies=row['document_tax_levies'] if 'document_tax_levies' in row.keys() else 0.0,
            items_tax_levies=row['items_tax_levies'] if 'items_tax_levies' in row.keys() else 0.0,
            shipping_cost=row['shipping_cost'] if 'shipping_cost' in row.keys() else 0.0,
            payable_amount=row['payable_amount'] if 'payable_amount' in row.keys() else 0.0,
            created_at=row['created_at'] if 'created_at' in row.keys() else None
        )
    
    def get_display_title(self) -> str:
        """عنوان نمایشی سند خرید"""
        if self.invoice_number:
            return f"فاکتور {self.invoice_number} - {self.supplier_name}"
        return f"خرید {self.document_row_number} - {self.supplier_name}"
    
    def __str__(self) -> str:
        return self.get_display_title()
    
    def __repr__(self) -> str:
        return f"CompanyPurchase(id={self.id}, invoice='{self.invoice_number}', supplier='{self.supplier_name}')"


class CompanyPurchaseItem:
    """مدل آیتم خرید شرکت"""
    
    def __init__(
        self,
        id: Optional[int] = None,
        purchase_document_id: int = 0,
        generic_code: str = '',
        brand_code: str = '',
        drug_name_snapshot: str = '',
        quantity_in_package: int = 0,
        package_count: int = 0,
        unit_count: int = 0,
        expiry_date_gregorian: str = '',
        expiry_date_jalali: str = '',
        purchase_price_per_package: float = 0.0,
        profit_percentage: float = 0.0,
        sale_price_per_package: float = 0.0,
        item_vat: float = 0.0,
        item_discount_rial: float = 0.0,
        batch_number: str = '',
        main_warehouse_location: str = '',
        main_warehouse_min_stock: int = 0,
        main_warehouse_max_stock: int = 0,
        created_at: Optional[str] = None
    ):
        self.id = id
        self.purchase_document_id = purchase_document_id
        self.generic_code = generic_code
        self.brand_code = brand_code
        self.drug_name_snapshot = drug_name_snapshot
        self.quantity_in_package = quantity_in_package
        self.package_count = package_count
        self.unit_count = unit_count
        self.expiry_date_gregorian = expiry_date_gregorian
        self.expiry_date_jalali = expiry_date_jalali
        self.purchase_price_per_package = purchase_price_per_package
        self.profit_percentage = profit_percentage
        self.sale_price_per_package = sale_price_per_package
        self.item_vat = item_vat
        self.item_discount_rial = item_discount_rial
        self.batch_number = batch_number
        self.main_warehouse_location = main_warehouse_location
        self.main_warehouse_min_stock = main_warehouse_min_stock
        self.main_warehouse_max_stock = main_warehouse_max_stock
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return {
            'id': self.id,
            'purchase_document_id': self.purchase_document_id,
            'generic_code': self.generic_code,
            'brand_code': self.brand_code,
            'drug_name_snapshot': self.drug_name_snapshot,
            'quantity_in_package': self.quantity_in_package,
            'package_count': self.package_count,
            'unit_count': self.unit_count,
            'expiry_date_gregorian': self.expiry_date_gregorian,
            'expiry_date_jalali': self.expiry_date_jalali,
            'purchase_price_per_package': self.purchase_price_per_package,
            'profit_percentage': self.profit_percentage,
            'sale_price_per_package': self.sale_price_per_package,
            'item_vat': self.item_vat,
            'item_discount_rial': self.item_discount_rial,
            'batch_number': self.batch_number,
            'main_warehouse_location': self.main_warehouse_location,
            'main_warehouse_min_stock': self.main_warehouse_min_stock,
            'main_warehouse_max_stock': self.main_warehouse_max_stock,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_db_row(cls, row) -> 'CompanyPurchaseItem':
        """ایجاد از row دیتابیس"""
        return cls(
            id=row['id'] if 'id' in row.keys() else None,
            purchase_document_id=row['purchase_document_id'] if 'purchase_document_id' in row.keys() else 0,
            generic_code=row['generic_code'] if 'generic_code' in row.keys() else '',
            brand_code=row['brand_code'] if 'brand_code' in row.keys() else '',
            drug_name_snapshot=row['drug_name_snapshot'] if 'drug_name_snapshot' in row.keys() else '',
            quantity_in_package=row['quantity_in_package'] if 'quantity_in_package' in row.keys() else 0,
            package_count=row['package_count'] if 'package_count' in row.keys() else 0,
            unit_count=row['unit_count'] if 'unit_count' in row.keys() else 0,
            expiry_date_gregorian=row['expiry_date_gregorian'] if 'expiry_date_gregorian' in row.keys() else '',
            expiry_date_jalali=row['expiry_date_jalali'] if 'expiry_date_jalali' in row.keys() else '',
            purchase_price_per_package=row['purchase_price_per_package'] if 'purchase_price_per_package' in row.keys() else 0.0,
            profit_percentage=row['profit_percentage'] if 'profit_percentage' in row.keys() else 0.0,
            sale_price_per_package=row['sale_price_per_package'] if 'sale_price_per_package' in row.keys() else 0.0,
            item_vat=row['item_vat'] if 'item_vat' in row.keys() else 0.0,
            item_discount_rial=row['item_discount_rial'] if 'item_discount_rial' in row.keys() else 0.0,
            batch_number=row['batch_number'] if 'batch_number' in row.keys() else '',
            main_warehouse_location=row['main_warehouse_location'] if 'main_warehouse_location' in row.keys() else '',
            main_warehouse_min_stock=row['main_warehouse_min_stock'] if 'main_warehouse_min_stock' in row.keys() else 0,
            main_warehouse_max_stock=row['main_warehouse_max_stock'] if 'main_warehouse_max_stock' in row.keys() else 0,
            created_at=row['created_at'] if 'created_at' in row.keys() else None
        )
    
    def calculate_total_purchase_price(self) -> float:
        """محاسبه قیمت کل خرید"""
        return self.purchase_price_per_package * self.package_count
    
    def calculate_total_sale_price(self) -> float:
        """محاسبه قیمت کل فروش"""
        return self.sale_price_per_package * self.package_count
    
    def calculate_profit_amount(self) -> float:
        """محاسبه مبلغ سود"""
        return self.calculate_total_sale_price() - self.calculate_total_purchase_price()
    
    def get_display_name(self) -> str:
        """نام نمایشی آیتم"""
        name = self.drug_name_snapshot
        if self.batch_number:
            name += f" (بچ: {self.batch_number})"
        return name
    
    def __str__(self) -> str:
        return f"{self.get_display_name()} - {self.package_count} بسته"
    
    def __repr__(self) -> str:
        return f"CompanyPurchaseItem(id={self.id}, drug='{self.drug_name_snapshot}', packages={self.package_count})"


# می‌تونی هر شی از بالا رو با کلاسش بسازی و در کل پروژه ازش استفاده کنی
