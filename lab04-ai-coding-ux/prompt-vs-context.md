# การทดลองเปรียบเทียบ Prompt Engineering กับ Context Engineering (Lab 04)

การทดลองนี้เป็นการเปรียบเทียบผลลัพธ์จากการสั่งงาน AI ในโจทย์เดียวกัน เพื่อศึกษาความแตกต่างระหว่างการสั่งงานแบบ **Prompt สั้น (ขาดบริบท)** กับการเตรียม **Context ที่ครบถ้วน (Context Engineering)**

---

## ตารางเปรียบเทียบองค์ประกอบคำสั่ง

| หัวข้อ | รอบที่ 1: Prompt สั้น (บกพร่อง) | รอบที่ 2: Prompt ที่มี Context ครบถ้วน |
| :--- | :--- | :--- |
| **ความชัดเจนของงาน** | "เขียน function ลด stock" | ระบุชื่อเมธอด `sell_many(orders: dict[str, int]) -> dict[str, int]`, ชนิด exception ที่ต้อง raise, การ rollback |
| **ความเข้ากันกับโค้ดเดิม** | ไม่ได้แนบโค้ดเดิมไปเลย | แนบคลาส `Inventory` และ `InventoryItem` ฉบับเดิมทั้งไฟล์ ให้ AI ยึด architecture |
| **เกณฑ์การตรวจสอบ** | ไม่ได้ระบุเงื่อนไขหรือ test case | แนบ test case การขายแบบ atomic (ถ้าชิ้นที่ 2 ไม่พอ ชิ้นที่ 1 ต้องไม่ถูกหัก) |
| **ข้อจำกัดของระบบ** | ไม่ได้ระบุ | ห้ามใช้ library ภายนอก และใช้ exception type เดียวกับระบบเดิม (`KeyError`, `ValueError`) |

---

## รอบที่ 1: สั่งงานด้วย Prompt สั้น ๆ (ไร้ Context)

### คำสั่งที่ใช้ (Prompt 1)
```text
เขียน function ลด stock ในระบบ inventory
```

### ผลลัพธ์โค้ดที่ AI สร้างให้ (Output 1)
```python
def reduce_stock(stock_dict, item_name, quantity):
    if item_name in stock_dict:
        if stock_dict[item_name] >= quantity:
            stock_dict[item_name] -= quantity
            return True
        else:
            print("Stock not enough")
            return False
    return False
```

### ปัญหาที่พบในรอบที่ 1
1. **ไม่เข้ากับโครงสร้างระบบเดิม**: AI สร้างฟังก์ชันลอย ๆ ที่รับพารามิเตอร์เป็น dictionary ธรรมดา แทนที่จะเป็นเมธอดในคลาส `Inventory`
2. **ไม่ใช้ Exception**: ใช้วิธีคืนค่า `True`/`False` และพิมพ์ `print()` แทนที่จะ raise `ValueError` หรือ `KeyError` ตามระบบเดิม
3. **ไม่รองรับการทำงานหลายรายการ (Batch/Atomic)**: ตัดสต็อกทีละรายการ ไม่สามารถรองรับโจทย์การขายหลายรายการพร้อมกันได้เลย

---

## รอบที่ 2: สั่งงานด้วย Prompt ที่แนบ Context ครบถ้วน (Context Engineering)

### คำสั่งที่ใช้ (Prompt 2)
```text
ปรับปรุงเมธอดของคลาส Inventory ด้านล่างให้รองรับการขายสินค้าหลายรายการพร้อมกัน

[Context: โค้ดเดิมของระบบ inventory.py ทั้งไฟล์]
class InventoryItem:
    def __init__(self, name: str, quantity: int, price: float):
        if not name or not name.strip():
            raise ValueError("ชื่อสินค้าต้องไม่ว่างเปล่า")
        if quantity < 0:
            raise ValueError("จำนวนสินค้าต้องไม่ติดลบ")
        if price <= 0:
            raise ValueError("ราคาต้องมากกว่าศูนย์")
        self.name = name.strip()
        self.quantity = quantity
        self.price = price

class Inventory:
    def __init__(self):
        self._items: dict[str, InventoryItem] = {}

    def add_item(self, name: str, quantity: int, price: float) -> InventoryItem:
        if name in self._items:
            raise ValueError(f"สินค้า '{name}' มีอยู่ในระบบแล้ว")
        item = InventoryItem(name, quantity, price)
        self._items[name] = item
        return item

    def restock(self, name: str, amount: int) -> int:
        if name not in self._items:
            raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
        if amount <= 0:
            raise ValueError("จำนวนที่เติมต้องมากกว่าศูนย์")
        self._items[name].quantity += amount
        return self._items[name].quantity

    def sell(self, name: str, amount: int) -> int:
        if name not in self._items:
            raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
        if amount <= 0:
            raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์")
        if self._items[name].quantity < amount:
            raise ValueError(
                f"สินค้า '{name}' คงเหลือ {self._items[name].quantity} ชิ้น\n"
                f"ไม่เพียงพอสำหรับการขาย {amount} ชิ้น"
            )
        self._items[name].quantity -= amount
        return self._items[name].quantity

    def get_total_value(self) -> float:
        return sum(
            item.quantity * item.price for item in self._items.values()
        )

ข้อกำหนด (Requirements & Constraints):
- เพิ่มเมธอด sell_many(orders: dict[str, int]) -> dict[str, int] คืน {ชื่อสินค้า: จำนวนคงเหลือ}
- ถ้ามีรายการใดรายการหนึ่ง stock ไม่พอ หรือไม่พบสินค้า ต้อง raise Exception และต้องไม่หักรายการใดเลย ทุกรายการต้องสำเร็จพร้อมกันหรือไม่สำเร็จเลย (Atomic / All-or-Nothing Transaction)
- ใช้ชนิด Exception แบบเดียวกับเมธอดเดิม (KeyError เมื่อไม่พบสินค้า, ValueError เมื่อสต็อกไม่พอหรือจำนวน <= 0)
- ห้ามใช้ library ภายนอก (Standard library เท่านั้น)

เกณฑ์การตรวจสอบ (Test Acceptance Criteria):
1. กรณีสต็อกพอทุกรายการ: หักยอดสินค้าทั้งหมด และคืนค่าคงเหลือของแต่ละสินค้าถูกต้อง
2. กรณีมีรายการใดรายการหนึ่งสต็อกไม่พอ (เช่น รายการที่ 2 ไม่พอ): ต้อง raise ValueError และรายการแรกที่ตรวจไปแล้วต้องไม่ถูกหักยอด (Rollback / No partial update)
```

### ผลลัพธ์โค้ดที่ AI สร้างให้ (Output 2)
```python
def sell_many(self, orders: dict[str, int]) -> dict[str, int]:
    """
    ขายสินค้าหลายรายการพร้อมกันแบบ Atomic (All-or-Nothing)
    คืนค่า {ชื่อสินค้า: จำนวนคงเหลือ}
    """
    # ขั้นตอนที่ 1: ตรวจสอบความถูกต้องและสต็อกของทุกรายการก่อนทำการตัดจริง (Pre-validation)
    for name, amount in orders.items():
        if name not in self._items:
            raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
        if amount <= 0:
            raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์")
        if self._items[name].quantity < amount:
            raise ValueError(
                f"สินค้า '{name}' คงเหลือ {self._items[name].quantity} ชิ้น "
                f"ไม่เพียงพอสำหรับการขาย {amount} ชิ้น"
            )

    # ขั้นตอนที่ 2: เมื่อทุกรายการผ่านเงื่อนไข จึงทำการตัดสต็อกจริง
    result = {}
    for name, amount in orders.items():
        self._items[name].quantity -= amount
        result[name] = self._items[name].quantity

    return result
```

---

## สรุปวิเคราะห์ผลลัพธ์: ความแตกต่างและสิ่งที่ทำให้ต่างกัน

### 1. ผลลัพธ์ของทั้งสองรอบต่างกันอย่างไร?
- **ความสมบูรณ์เชิงสถาปัตยกรรม (Architectural Consistency)**:
  - ในรอบที่ 1 โค้ดที่ได้ไม่สามารถนำมาเสียบใช้งานกับโปรเจกต์เดิมได้เลย ต้องมาเขียนเชื่อมโยงใหม่ทั้งหมด
  - ในรอบที่ 2 โค้ดที่ได้สอดคล้องกับคลาส `Inventory` ทันที สามารถคัดลอกไปวางในคลาสเดิมได้เลยอย่างไร้รอยต่อ
- **การจัดการความถูกต้องของข้อมูล (Atomicity & Reliability)**:
  - ในรอบที่ 1 ไม่มีการคิดถึงกรณีข้อผิดพลาดกึ่งกลางคัน
  - ในรอบที่ 2 AI ทำงานแบบ **Two-phase commit / Pre-validation** คือตรวจเช็กสต็อกของทุกรายการใน `orders` ให้ครบก่อน หากมีข้อผิดพลาดจะโยน Exception ทันทีโดยที่ยังไม่มีรายการใดถูกหักยอด ทำให้ข้อมูลในระบบไม่เสียหาย (Atomic Transaction)
- **การปฏิบัติตาม Convention เดิม**:
  - รอบที่ 2 มีการใช้ `KeyError` และ `ValueError` พร้อมข้อความแจ้งเตือนที่ตรงกับมาตรฐานเดิมของโปรเจกต์

### 2. อะไรทำให้ผลลัพธ์ต่างกัน?
- **Prompt Engineering** ช่วยกำหนด "ความต้องการและเป้าหมาย" (What to do) ให้ชัดเจน แต่ถ้ามีเฉพาะคำสั่ง AI จะเดาบริบทแวดล้อมเอาเอง ซึ่งมักจะได้ผลลัพธ์ที่เป็น Generic Code
- **Context Engineering** คือปัจจัยชี้ขาด เพราะการแนบ **โค้ดเดิม (Existing Codebase)**, **ข้อจำกัด (Constraints)** และ **เกณฑ์การทดสอบ (Test Expectations)** ไปด้วย ทำให้ AI มี "กรอบอ้างอิง (Frame of Reference)" ที่ชัดเจน ส่งผลให้โค้ดที่สร้างออกมาตรงสเปก ทำงานได้จริง และปลอดภัยต่อระบบโดยไม่ต้องเสียเวลาแก้ไขซ้ำหลายรอบ
