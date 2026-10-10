# แผนภาพสถาปัตยกรรมระบบ (System Architecture Diagrams)

เอกสารรวบรวม Class Diagram และ Sequence Diagram ของระบบคลังสินค้า (`swe-inventory`)

---

## 1. Class Diagram

แสดงโครงสร้างคลาส ความสัมพันธ์ และเมธอดหลักของระบบคลังสินค้าและระบบคิดคำนวณราคา:

```mermaid
classDiagram
    class InventoryItem {
        +str name
        +int quantity
        +float price
        +__init__(name: str, quantity: int, price: float)
    }

    class Inventory {
        -dict _items
        +add_item(name: str, quantity: int, price: float) InventoryItem
        +restock(name: str, amount: int) int
        +sell(name: str, amount: int) int
        +get_total_value() float
        +low_stock_items(threshold: int) list~str~
    }

    class PricingService {
        <<module>>
        +calc(items, member, coupon, today) float
        +calculate_items_subtotal(items) float
        +apply_member_benefits(subtotal, member) float
        +apply_coupon_discount(subtotal, coupon, today) float
        +apply_tax_and_rounding(amount) float
    }

    Inventory "1" *-- "*" InventoryItem : contains
    Inventory ..> PricingService : calculates total price
```

---

## 2. Sequence Diagram (กระบวนการขายและคิดราคา)

แสดงลำดับการทำงาน (Workflow) เมื่อลูกค้าทำการซื้อสินค้าในระบบ พร้อมการคิดส่วนลดและบันทึกประวัติ Transaction:

```mermaid
sequenceDiagram
    autonumber
    actor Customer as ลูกค้า / ผู้ใช้งาน
    participant Inv as Inventory System
    participant Pricing as Pricing Module
    participant Audit as LOG & Member Points

    Customer->>Inv: sell(item_name, quantity)
    alt สินค้าไม่มีในระบบ
        Inv-->>Customer: raise KeyError("ไม่พบสินค้า")
    else จำนวนสินค้าในคลังไม่เพียงพอ
        Inv-->>Customer: raise ValueError("สินค้าคงเหลือไม่เพียงพอ")
    else สต็อกสินค้าเพียงพอ
        Inv->>Inv: ตัดยอดสินค้าคงเหลือ (quantity -= amount)
        Inv-->>Customer: คืนค่ายอดคงเหลือหลังการขาย
    end

    Customer->>Pricing: calc(items, member, coupon, today)
    Pricing->>Pricing: 1. คำนวณราคาตามปริมาณ (Bulk Discount 5%-10%)
    Pricing->>Pricing: 2. หักส่วนลดสมาชิก 5% (ถ้ามี)
    Pricing->>Audit: บันทึกแต้มสะสมสมาชิก (1 แต้ม ต่อ 100 บาท)
    Pricing->>Pricing: 3. ตรวจสอบคูปอง (SAVE50 / HALF / NEWYEAR)
    Pricing->>Pricing: 4. ป้องกันยอดติดลบ และบวกภาษี VAT 7%
    Pricing->>Audit: บันทึกรายการลงใน LOG
    Pricing-->>Customer: คืนราคาสุทธิหลังหักส่วนลดและภาษี (final_price)
```
