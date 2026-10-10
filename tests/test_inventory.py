import pytest

from inventory import Inventory, InventoryItem

# =====================================================================
# ขั้นที่ 2: TDD Tests สำหรับเมธอด low_stock_items (ครบ 6 กรณี)
# =====================================================================

def test_low_stock_items_all_above_threshold():
    """กรณีที่ 1: สินค้าทุกรายการมีจำนวนมากกว่า threshold -> คืน list ว่าง"""
    inv = Inventory()
    inv.add_item("Apple", 10, 20.0)
    inv.add_item("Banana", 15, 10.0)
    assert inv.low_stock_items(5) == []


def test_low_stock_items_exact_threshold():
    """กรณีที่ 2: มีสินค้าที่จำนวนเท่ากับ threshold พอดี -> ต้องถูกนับรวมด้วย"""
    inv = Inventory()
    inv.add_item("Apple", 5, 20.0)
    inv.add_item("Banana", 10, 10.0)
    assert inv.low_stock_items(5) == ["Apple"]


def test_low_stock_items_multiple_items_sorted_by_name():
    """กรณีที่ 3: มีสินค้าเข้าเกณฑ์หลายรายการ -> ผลลัพธ์เรียงตามชื่อ ไม่ใช่ตามลำดับที่เพิ่ม"""
    inv = Inventory()
    inv.add_item("Orange", 3, 25.0)
    inv.add_item("Apple", 2, 20.0)
    inv.add_item("Mango", 4, 30.0)
    inv.add_item("Watermelon", 50, 15.0)
    assert inv.low_stock_items(5) == ["Apple", "Mango", "Orange"]


def test_low_stock_items_empty_inventory():
    """กรณีที่ 4: คลังว่าง -> คืน list ว่าง ไม่ใช่ error"""
    inv = Inventory()
    assert inv.low_stock_items(10) == []


def test_low_stock_items_threshold_zero():
    """กรณีที่ 5: threshold เป็น 0 -> คืนเฉพาะสินค้าที่เหลือ 0"""
    inv = Inventory()
    inv.add_item("Apple", 0, 20.0)
    inv.add_item("Banana", 5, 10.0)
    assert inv.low_stock_items(0) == ["Apple"]


def test_low_stock_items_negative_threshold():
    """กรณีที่ 6: threshold ติดลบ -> คืน error ValueError("threshold ต้องไม่ติดลบ")"""
    inv = Inventory()
    inv.add_item("Apple", 5, 20.0)
    with pytest.raises(ValueError, match="threshold ต้องไม่ติดลบ"):
        inv.low_stock_items(-1)


# =====================================================================
# ขั้นที่ 4: Tests สำหรับเมธอด sell (AI Baseline + Edge Cases เสริม)
# =====================================================================

def test_sell_normal_flow_ai_baseline():
    """กรณีปกติที่ AI มักเขียนให้: ขายสินค้าสำเร็จและยอดลดลงตามจริง"""
    inv = Inventory()
    inv.add_item("Apple", 10, 20.0)
    remaining = inv.sell("Apple", 3)
    assert remaining == 7
    assert inv._items["Apple"].quantity == 7


def test_sell_exact_remaining_boundary():
    """กลุ่มที่ 1 ค่าขอบ: ขายเท่ากับจำนวนที่เหลือทั้งหมดได้ไหม แล้วเหลือเท่าไร (เหลือ 0 พอดี)"""
    inv = Inventory()
    inv.add_item("Apple", 5, 20.0)
    remaining = inv.sell("Apple", 5)
    assert remaining == 0
    assert inv._items["Apple"].quantity == 0


def test_sell_zero_quantity():
    """กลุ่มที่ 2 ค่าที่ไม่ควรรับ: ขายจำนวน 0 ต้องไม่อนุญาตและ raise ValueError"""
    inv = Inventory()
    inv.add_item("Apple", 10, 20.0)
    with pytest.raises(ValueError, match="จำนวนที่ขายต้องมากกว่าศูนย์"):
        inv.sell("Apple", 0)


def test_sell_negative_quantity():
    """กลุ่มที่ 2 ค่าที่ไม่ควรรับ: ขายจำนวนติดลบ ต้องไม่อนุญาตและ raise ValueError"""
    inv = Inventory()
    inv.add_item("Apple", 10, 20.0)
    with pytest.raises(ValueError, match="จำนวนที่ขายต้องมากกว่าศูนย์"):
        inv.sell("Apple", -5)


def test_sell_nonexistent_item_keyerror():
    """กลุ่มที่ 3 เส้นทาง error: ขายสินค้าที่ไม่มีในคลัง ต้องได้ KeyError พร้อมชื่อสินค้า"""
    inv = Inventory()
    inv.add_item("Apple", 10, 20.0)
    with pytest.raises(KeyError, match="ไม่พบสินค้า 'Orange' ในระบบ"):
        inv.sell("Orange", 1)


def test_sell_exceeding_stock_error_message():
    """กลุ่มที่ 3 เส้นทาง error: ขายเกินจำนวนที่มี ต้องได้ ValueError พร้อมข้อความระบุยอดชัดเจน"""
    inv = Inventory()
    inv.add_item("Apple", 5, 20.0)
    with pytest.raises(ValueError, match="สินค้า 'Apple' คงเหลือ 5 ชิ้น"):
        inv.sell("Apple", 10)


def test_sell_invalid_type_string_raises_error():
    """กลุ่มที่ 4 ชนิดข้อมูล: ใส่จำนวนเป็นข้อความ ต้องเกิด TypeError"""
    inv = Inventory()
    inv.add_item("Apple", 10, 20.0)
    with pytest.raises(TypeError):
        inv.sell("Apple", "two")


# =====================================================================
# Tests เพิ่มเติมเพื่อให้ระบบครอบคลุมและผ่านเกณฑ์ CI Coverage (> 85%)
# =====================================================================

def test_inventory_item_validation():
    """ทดสอบการตรวจสอบข้อมูลตอนสร้าง InventoryItem"""
    with pytest.raises(ValueError, match="ชื่อสินค้าต้องไม่ว่างเปล่า"):
        InventoryItem("", 10, 100.0)
    with pytest.raises(ValueError, match="จำนวนสินค้าต้องไม่ติดลบ"):
        InventoryItem("Item", -1, 100.0)
    with pytest.raises(ValueError, match="ราคาต้องมากกว่าศูนย์"):
        InventoryItem("Item", 10, 0.0)


def test_add_item_duplicate():
    """ทดสอบการเพิ่มสินค้าที่มีชื่อซ้ำในระบบ"""
    inv = Inventory()
    inv.add_item("Apple", 10, 20.0)
    with pytest.raises(ValueError, match="สินค้า 'Apple' มีอยู่ในระบบแล้ว"):
        inv.add_item("Apple", 5, 20.0)


def test_restock_success_and_errors():
    """ทดสอบการเติมสต็อกสินค้ากรณีปกติและกรณีเกิด error"""
    inv = Inventory()
    inv.add_item("Apple", 10, 20.0)

    # เติมปกติ
    new_qty = inv.restock("Apple", 5)
    assert new_qty == 15
    assert inv._items["Apple"].quantity == 15

    # เติมจำนวน <= 0
    with pytest.raises(ValueError, match="จำนวนที่เติมต้องมากกว่าศูนย์"):
        inv.restock("Apple", 0)

    # เติมสินค้าที่ไม่มีในระบบ
    with pytest.raises(KeyError, match="ไม่พบสินค้า 'Banana' ในระบบ"):
        inv.restock("Banana", 5)


def test_get_total_value():
    """ทดสอบการคำนวณมูลค่ารวมสินค้าในคลัง"""
    inv = Inventory()
    inv.add_item("Apple", 10, 20.0)   # 200.0
    inv.add_item("Banana", 5, 10.0)   # 50.0
    assert inv.get_total_value() == 250.0
