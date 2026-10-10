# เฉลยและคำตอบแบบฝึกหัดส่งท้าย (Lab 04)

---

### ข้อ 1: วิเคราะห์ bug ในส่วนที่ 2 ที่รันได้ปกติในกรณีทั่วไป แต่พังเฉพาะใน edge case หรือเมื่อหลาย thread ทำงานพร้อมกัน ยกมา 2 ข้อ พร้อมอธิบายว่าทำไม test ธรรมดาจึงจับไม่เจอ

#### ตัวอย่างที่ 1: `concurrent_restock` (Race Condition / Lost Update จากการอ่านค่านอกบล็อก Lock)
- **พฤติกรรม**: โค้ดอ่านค่า `current = self._inv._items[name].quantity` นอกบล็อก `with self._lock:` แล้วจึงเข้าไปอัปเดตค่าในบล็อกล็อก
- **ทำไม Unit Test ทั่วไปถึงจับไม่เจอ**:
  Unit Test ธรรมดาทำงานแบบ Single Thread (รันตามลำดับทีละบรรทัด Synchronous) ทำให้การอ่านค่านอกล็อกและเขียนค่าในล็อกทำงานติดต่อกันเสร็จสิ้นเสมอโดยไม่มีการแย่งชิงทรัพยากร (No Interleaving) ผลลัพธ์จึงออกมาถูกต้อง 100% แต่เมื่อนำไปรันในสภาพแวดล้อมจริงที่มีหลายคำขอจากผู้ใช้เข้ามาพร้อมกัน (Multi-threaded) ตัวแปร `current` ของแต่ละ Thread จะอ่านค่าเก่าอันเดียวกัน ส่งผลให้เกิดการเขียนทับ (Lost Update) ทันที

#### ตัวอย่างที่ 2: `sell_batch` (ขาด Transaction Atomicity เมื่อเกิดข้อผิดพลาดกึ่งกลางคัน)
- **พฤติกรรม**: วนลูปตัดสต็อกสินค้าทีละชิ้น หากรายการใดรายการหนึ่งสต็อกไม่พอ จะเกิด Exception หลุดออกมาทันที โดยที่รายการก่อนหน้าถูกหักสต็อกไปเรียบร้อยแล้ว
- **ทำไม Unit Test ทั่วไปถึงจับไม่เจอ**:
  Unit Test ส่วนใหญ่มักทดสอบเฉพาะกรณี Happy Path (สต็อกเพียงพอทุกรายการ ซึ่งทดสอบแล้วผ่านฉลุย) หรือหากทดสอบกรณีสินค้าไม่พอ ก็มักจะตรวจสอบเพียงแค่ว่าฟังก์ชันโยน `ValueError` หรือไม่ (`pytest.raises(ValueError)`) ซึ่งก็ผ่านเช่นกัน แต่ Test ธรรมดาไม่ได้เขียน Assertion ย้อนกลับไปตรวจเช็กว่า **"สต็อกของสินค้าตัวแรกถูกหักไปหรือไม่"** จึงไม่เห็นว่าข้อมูลในฐานข้อมูลถูกแก้ไขจนเพี้ยนไปแล้ว

---

### ข้อ 2: ออกแบบ test ที่จับ bug จากการทำงานพร้อมกันของหลาย thread มาหนึ่งข้อ พร้อมเขียน test case และอธิบายการจำลอง

เลือกเมธอด: **`concurrent_restock`** ในคลาส `InventoryService`

#### โค้ดทดสอบด้วย Pytest (`test_concurrent_restock_race_condition.py`)
```python
import threading
from inventory import Inventory
from inventory_service import InventoryService


def test_concurrent_restock_lost_update():
    # 1. Setup: สร้างคลังสินค้าและกำหนดสต็อกเริ่มต้นเป็น 0
    inv = Inventory()
    inv.add_item("Book A", quantity=0, price=100.0)
    service = InventoryService(inv)

    # 2. กำหนดให้ 10 Threads แต่ละ Thread เติมของครั้งละ 1 ชิ้น จำนวน 100 รอบ (รวมควรได้ 1,000 ชิ้น)
    NUM_THREADS = 10
    ITERATIONS_PER_THREAD = 100

    def restock_worker():
        for _ in range(ITERATIONS_PER_THREAD):
            service.concurrent_restock("Book A", 1)

    threads = [threading.Thread(target=restock_worker) for _ in range(NUM_THREADS)]

    # 3. เริ่มรันทุก Thread พร้อมกัน
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 4. Assert: ยอดสต็อกสุดท้ายต้องเท่ากับ 1,000 ชิ้นพอดิบพอดี
    expected_total = NUM_THREADS * ITERATIONS_PER_THREAD
    actual_total = inv._items["Book A"].quantity

    # หากโค้ดมีบั๊ก Lost Update ค่า actual_total จะได้น้อยกว่า 1,000 อย่างมีนัยสำคัญ
    assert actual_total == expected_total, (
        f"เกิด Race Condition! คาดหวัง {expected_total} ชิ้น แต่ได้ {actual_total} ชิ้น"
    )
```

#### อธิบายวิธีการจำลองการทำงานพร้อมกัน
1. ใช้ `threading.Thread` สร้างชุดของเธรดจำนวนมาก (เช่น 10 เธรด) เพื่อเพิ่มโอกาสการแทรกแทรงจังหวะเวลา (Context Switch) ระหว่างการอ่านค่า `current` และการเข้าบล็อก `lock`
2. ให้แต่ละเธรดวนลูปเติมสต็อกซ้ำๆ หลายครั้ง ซึ่งเป็นการกระตุ้นให้ CPU สลับ Core/Thread บ่อยครั้งที่สุด
3. ใช้ `t.join()` เพื่อรอให้ทุกเธรดทำงานจบ แล้วจึงตรวจสอบผลรวมสุดท้าย หากค่าที่ได้น้อยกว่ายอดรวมที่คาดหวัง แสดงว่าเกิด Lost Update ขึ้นจริง

---

### ข้อ 3: ประเมิน AI จากการเทียบ review ของตัวเองกับของ AI และการแบ่งงานอย่างปลอดภัย

#### AI Reviewer ทำได้ดีในด้านใด:
- ตรวจสอบรูปแบบโค้ด (Coding Conventions, Formatting, PEP 8)
- จับข้อผิดพลาดทางเทคนิคทั่วไป เช่น ตัวแปรที่ไม่ได้ใช้ (Unused variables), ไวยากรณ์ผิด, หรือการเกิด `ZeroDivisionError` ชัดเจนในบรรทัดตรงไปตรงมา
- ช่วยแนะนำการเขียน Docstring และ Type Hinting ให้สมบูรณ์ขึ้น

#### AI Reviewer พลาดในด้านใด:
- **Concurrency & Race Conditions**: AI มักเห็นแค่ว่า "มี Lock แล้ว" ก็ด่วนสรุปว่า Thread-safe โดยไม่เข้าใจว่าจุดที่อ่านตัวแปรอยู่นอกบล็อก Synchronization
- **Business Logic & Edge Cases**: ขาดความเข้าใจบริบททางธุรกิจ เช่น การคำนวณราคาปิดช่วง `[low, high]` หรือการที่คำสั่งซื้อต้องสมบูรณ์แบบ Atomic
- **Semantic Hallucination**: บางครั้ง AI เข้าใจผิดว่า `len(items)` คือจำนวนชิ้นสินค้า ทั้งที่เป็นจำนวนชนิดสินค้า (SKU)

#### ข้อเสนอแนะในการแบ่งงาน Review ระหว่างมนุษย์กับ AI อย่างปลอดภัย:
1. **ให้ AI ทำ First-pass Static Scan**: มอบหมายให้ AI ทำหน้าที่เป็น Linter / Scanner รอบแรก ตรวจสอบ Code Style, Documentation, และ Syntax Errors พื้นฐาน ช่วยลดภาระงานรูทีนของโปรแกรมเมอร์
2. **มนุษย์ (Software Engineer) ตรวจสอบ Deep Logic**: คนต้องเป็นผู้ตัดสินใจและโฟกัสที่ Architecture, Business Logic, Boundary Conditions (Off-by-one), Atomicity/Rollback, Security สิทธิ์การเข้าถึงข้อมูล และ Multi-threading Concurrency
3. **กำหนดเกณฑ์ห้ามเชื่อผล AI 100% (Zero-Trust)**: ทุกการอนุมัติ Pull Request (Approve & Merge) ต้องมีวิศวกรซอฟต์แวร์ที่เป็นมนุษย์ลงชื่อรับรองเสมอ

---

### ข้อ 4: สะท้อนคิด (Reflection: 100–150 คำ) ทักษะการตรวจงานที่ AI ทำสำคัญอย่างไร เมื่อเทียบกับการพิมพ์โค้ดเอง

> ทักษะการตรวจงานที่ AI ทำมีความสำคัญอย่างยิ่งและกลายเป็นหัวใจหลักของวิศวกรซอฟต์แวร์ยุคปัจจุบัน เพราะ AI สามารถสร้างโค้ดที่มีหน้าตาเรียบร้อย รันผ่าน และดูน่าเชื่อถือได้อย่างรวดเร็ว แต่เบื้องหลังกลับซ่อนบั๊กที่ร้ายแรง เช่น การอ่านค่านอกบล็อก Lock ใน `concurrent_restock` หรือการขาดระบบ Rollback ใน `sell_batch` ซึ่งการทดสอบทั่วไปจับไม่เจอ หากเรามีทักษะเพียงแค่การสั่งงานหรือการพิมพ์โค้ดเร็ว แต่ขาดความลึกซึ้งในการอ่านโค้ด การทำ Debugging แบบมีหลักฐาน และการวิเคราะห์ Edge Case ระบบที่นำขึ้นใช้งานจริงจะพังทลายและสร้างความเสียหายอย่างมหาศาล ดังนั้นบทบาทของโปรแกรมเมอร์จึงเปลี่ยนจากการเป็น "ผู้พิมพ์โค้ด" ไปสู่การเป็น "ผู้กำกับและผู้ตรวจสอบ (Gatekeeper)" ที่ต้องใช้หลักฐานและตรรกะในการรับประกันความปลอดภัยของระบบ
