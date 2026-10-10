import pytest
from inventory import Inventory


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
