# บันทึกการ Debugging แบบมีหลักฐาน (Evidence-Based Debug Log)

เอกสารบันทึกการสืบสวนหา **Root Cause** และแก้ปัญหา Bug ในโมดูล `discount.py` ตามกระบวนการ 5 ขั้นตอนอย่างเป็นระบบ

---

## สรุปภาพรวมผลการรัน Test ครั้งแรก (Reproduce)
คำสั่งที่ใช้รัน: `python -m pytest tests/ -v`
ผลลัพธ์: **4 Failed, 2 Passed**
- `test_apply_discount_basic`: **FAILED** (`assert 99.9 == 90.0`)
- `test_apply_discount_zero`: **PASSED** *(⚠️ กับดัก! ผ่านทั้งที่สูตรผิด)*
- `test_bulk_total`: **FAILED** (`assert 299.9 == 270.0`)
- `test_average_price`: **PASSED**
- `test_average_price_empty`: **FAILED** (`ZeroDivisionError: division by zero`)
- `test_cheapest_n`: **FAILED** (`assert [20.0] == [10.0, 20.0]`)

---

## การไล่หา Root Cause ทีละจุด

### จุดที่ 1: `test_apply_discount_basic`

#### 1. Reproduce
- คำสั่ง: `python -m pytest tests/test_discount.py::test_apply_discount_basic -v`
- Assertion ที่ fail:
  ```text
  > assert apply_discount(100.0, 10) == 90.0
  E assert 99.9 == 90.0
  E  + where 99.9 = apply_discount(100.0, 10)
  ```

#### 2. Traceback
- ตำแหน่งที่เกิด: ไฟล์ `discount.py` บรรทัดที่ 5 ในฟังก์ชัน `apply_discount`
  ```python
  return price - percent / 100
  ```

#### 3. สมมติฐาน
สมมติฐานคือ สูตรการคำนวณส่วนลดใช้ตัวดำเนินการผิด โดยนำ `price` ไปลบกับ `percent / 100` โดยตรง แทนที่จะนำไปลบกับ "จำนวนเงินส่วนลดจริง" ซึ่งคือ `price * (percent / 100)` ทำให้เมื่อคิดลด 10% จาก 100 บาท ระบบคำนวณเป็น `100 - (10 / 100) = 100 - 0.1 = 99.9` แทนที่จะได้ `90.0`

#### 4. การยืนยัน
ทดสอบพิมพ์ค่าใน Interactive Python:
```python
price = 100.0
percent = 10
print("สูตรเดิม:", price - percent / 100) # ได้ 99.9
print("สูตรที่ถูกต้อง:", price * (1 - percent / 100)) # ได้ 90.0
```
ค่าที่ได้ห่างจากที่คาดหวังมาก ยืนยันว่าเกิดจากการใช้สูตรคำนวณผิดความหมาย

#### 5. Root Cause และการแก้
- **Root Cause**: ผู้พัฒนาเขียนสูตรคณิตศาสตร์ผิด โดยขาดตัวคูณ `price` กับอัตราส่วนลด ทำให้กลายเป็นการลบค่าเปอร์เซ็นต์ในรูปทศนิยมออกจากราคาโดยตรง
- **การแก้ไข**: แก้ไขสูตรคำนวณเป็น:
  ```python
  return price * (1 - percent / 100)
  ```

---

### จุดที่ 2: `test_bulk_total`

#### 1. Reproduce
- คำสั่ง: `python -m pytest tests/test_discount.py::test_bulk_total -v`
- Assertion ที่ fail:
  ```text
  > assert bulk_total([100.0, 100.0, 100.0], 10) == 270.0
  E assert 299.9 == 270.0
  E  + where 299.9 = bulk_total([100.0, 100.0, 100.0], 10)
  ```

#### 2. Traceback
- ตำแหน่งที่เกิด: เกิดขึ้นที่ฟังก์ชัน `bulk_total` บรรทัดที่ 12 ซึ่งเรียกต่อไปยัง `apply_discount`
  ```python
  return apply_discount(total, discount_percent)
  ```

#### 3. สมมติฐาน
ฟังก์ชัน `bulk_total` รวมยอดราคาสินค้าได้ถูกต้องแล้ว (`total = 300.0`) แต่ผลลัพธ์ล้มเหลวเพราะเป็นผลกระทบลูกโซ่ (Cascading Failure) มาจากบั๊กในฟังก์ชัน `apply_discount` ที่คำนวณ `300 - 10/100 = 299.9`

#### 4. การยืนยัน
ทดลองตรวจสอบค่า `total` ก่อนส่งเข้า `apply_discount`:
```python
total = sum([100.0, 100.0, 100.0])
print("total:", total) # 300.0 ถูกต้อง
```
เมื่อทดสอบส่งค่า `total = 300.0` เข้าฟังก์ชัน `apply_discount` ที่แก้สูตรแล้ว:
`300.0 * (1 - 10 / 100) = 270.0` ตรงตาม assertion ทุกประการ

#### 5. Root Cause และการแก้
- **Root Cause**: ฟังก์ชัน `apply_discount` ที่เป็น Dependency มีสูตรคำนวณผิดพลาด
- **การแก้ไข**: เมื่อแก้ไข `apply_discount` ให้ถูกต้องแล้ว ฟังก์ชัน `bulk_total` จะผ่านการทดสอบโดยอัตโนมัติ

---

### จุดที่ 3: `test_average_price_empty`

#### 1. Reproduce
- คำสั่ง: `python -m pytest tests/test_discount.py::test_average_price_empty -v`
- Assertion ที่ fail:
  ```text
  > assert average_price([]) == 0.0
  E ZeroDivisionError: division by zero
  ```

#### 2. Traceback
- ตำแหน่งที่เกิด: ไฟล์ `discount.py` บรรทัดที่ 18 ในฟังก์ชัน `average_price`
  ```python
  return sum(prices) / len(prices)
  ```

#### 3. สมมติฐาน
ฟังก์ชัน `average_price` ขาดการตรวจสอบ Guard Clause กรณีที่ลิสต์ `prices` ว่างเปล่า (`[]`) ทำให้ `len(prices)` มีค่าเป็น 0 เมื่อนำไปเป็นตัวหารจึงทำให้ Python โยนข้อยกเว้น `ZeroDivisionError`

#### 4. การยืนยัน
ทดสอบตรวจสอบเงื่อนไขความยาว:
```python
prices = []
print(bool(prices)) # False
print(len(prices))  # 0 -> เมื่อเอาไปหารจะเกิด ZeroDivisionError
```

#### 5. Root Cause และการแก้
- **Root Cause**: ไม่มีการดักกรณี Edge Case เมื่อข้อมูลนำเข้าเป็นลิสต์ว่าง (`len == 0`)
- **การแก้ไข**: เพิ่มเงื่อนไขตรวจสอบว่าหากไม่มีข้อมูล ให้คืนค่า `0.0`:
  ```python
  def average_price(prices: list) -> float:
      """คืนราคาเฉลี่ยของรายการสินค้า"""
      if not prices:
          return 0.0
      return sum(prices) / len(prices)
  ```

---

### จุดที่ 4: `test_cheapest_n`

#### 1. Reproduce
- คำสั่ง: `python -m pytest tests/test_discount.py::test_cheapest_n -v`
- Assertion ที่ fail:
  ```text
  > assert cheapest_n([50.0, 10.0, 30.0, 20.0], 2) == [10.0, 20.0]
  E assert [20.0] == [10.0, 20.0]
  E   At index 0 diff: 20.0 != 10.0
  E   Right contains one more item: 20.0
  ```

#### 2. Traceback
- ตำแหน่งที่เกิด: ไฟล์ `discount.py` บรรทัดที่ 24 ในฟังก์ชัน `cheapest_n`
  ```python
  ordered = sorted(prices)
  return ordered[1:n]
  ```

#### 3. สมมติฐาน
ฟังก์ชันทำการ Slice ลิสต์ผิด Index (Off-by-one Error) โดยใช้ `ordered[1:n]` ในภาษา Python Index เริ่มต้นที่ 0 ดังนั้นการตัดที่ Index 1 จะทำให้ตัวที่ราคาถูกที่สุดจริง ๆ (Index 0 คือ 10.0) หายไป และช่วง `1:2` จะได้สมาชิกเพียงตัวเดียวคือ `[20.0]` แทนที่จะได้ `[10.0, 20.0]`

#### 4. การยืนยัน
ทดลองรันคำสั่ง Slice บนข้อมูลตัวอย่าง:
```python
ordered = sorted([50.0, 10.0, 30.0, 20.0]) # [10.0, 20.0, 30.0, 50.0]
print("เดิม [1:2]:", ordered[1:2]) # ได้ [20.0] (ผิด)
print("แก้เป็น [:2]:", ordered[:2]) # ได้ [10.0, 20.0] (ถูกต้อง)
```

#### 5. Root Cause และการแก้
- **Root Cause**: ความสับสนในการระบุจุดเริ่มต้นของ Slicing ซึ่งใน Python ต้องเริ่มจาก Index `0`
- **การแก้ไข**: แก้ไขให้ Slice ตั้งแต่เริ่มต้นจนถึงตำแหน่งที่ `n` ด้วย `ordered[:n]`:
  ```python
  def cheapest_n(prices: list, n: int) -> list:
      """คืน n รายการที่ราคาถูกที่สุด เรียงจากถูกไปแพง"""
      ordered = sorted(prices)
      return ordered[:n]
  ```

---

## การวิเคราะห์กับดัก (Deliberate Trap): `test_apply_discount_zero`

- **ข้อสังเกต**: ในการรันครั้งแรก `test_apply_discount_zero` ผ่านการทดสอบ (`PASSED`)
  ```python
  def test_apply_discount_zero():
      assert apply_discount(250.0, 0) == 250.0
  ```
- **ทำไมถึงเป็นกับดัก?**:
  สูตรเดิมของ AI คือ `price - percent / 100` เมื่อส่ง `percent = 0` เข้าไป:
  `250.0 - 0 / 100 = 250.0 - 0.0 = 250.0`
  ซึ่งทำให้ผลลัพธ์บังเอิญเท่ากับคำตอบที่คาดหวังพอดิบพอดี!
- **บทเรียนทางวิศวกรรมซอฟต์แวร์**:
  **"การที่ Test Case ผ่าน ไม่ได้การันตีว่าฟังก์ชันนั้นถูกต้องเสมอไป"** หากชุดทดสอบครอบคลุมเฉพาะค่าขอบที่เป็นศูนย์ (Corner Case) ที่บังเอิญให้ผลลัพธ์ตรงกัน การเขียน Unit Test จึงต้องมี Test Coverage ที่หลากหลายทั้งกรณีทั่วไป (Happy Path) และ Edge Cases เพื่อไม่ให้บั๊กเล็ดลอดไปได้
