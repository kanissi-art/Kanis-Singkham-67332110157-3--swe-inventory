import datetime

import pytest

from pricing import LOG, calc, member_points


@pytest.fixture(autouse=True)
def reset_globals():
    """ล้างสถานะตัวแปรส่วนกลาง (Shared Mutable State) ก่อนเริ่มทุก test"""
    member_points.clear()
    LOG.clear()
    yield
    member_points.clear()
    LOG.clear()


# =====================================================================
# 1. กลุ่มราคาปกติ (Normal Price)
# =====================================================================
def test_pricing_normal_single_item():
    """สินค้าหนึ่งรายการ จำนวนน้อย ไม่ใช้สิทธิ์ใดๆ"""
    items = [("Book", 2, 100.0)]
    result = calc(items)
    assert result == 214.0


# =====================================================================
# 2. กลุ่มซื้อจำนวนมาก (Bulk Purchase)
# =====================================================================
def test_pricing_bulk_below_first_tier():
    """จำนวน 49 ชิ้น (ยังไม่ถึงเกณฑ์ขั้นต่ำ 50 ชิ้น) คิดราคาเต็มไม่มีส่วนลด"""
    items = [("Pen", 49, 10.0)]
    result = calc(items)
    assert result == 524.3


def test_pricing_bulk_exact_50_items_tier():
    """จำนวน 50 ชิ้นพอดี (เกณฑ์ลด 5%)"""
    items = [("Pen", 50, 10.0)]
    result = calc(items)
    assert result == 508.25


def test_pricing_bulk_between_50_and_100():
    """จำนวน 99 ชิ้น (เกณฑ์ลด 5%)"""
    items = [("Pen", 99, 10.0)]
    result = calc(items)
    assert result == 1006.34


def test_pricing_bulk_exact_100_items_tier():
    """จำนวน 100 ชิ้นพอดี (เกณฑ์ลด 10%)"""
    items = [("Pen", 100, 10.0)]
    result = calc(items)
    assert result == 963.0


# =====================================================================
# 3. กลุ่มจำนวนเป็นศูนย์หรือติดลบ (Zero and Negative Quantity)
# =====================================================================
def test_pricing_zero_quantity():
    """สินค้าที่ใส่จำนวน 0 ชิ้น"""
    items = [("Book", 0, 100.0)]
    result = calc(items)
    assert result == 0.0


def test_pricing_negative_quantity():
    """สินค้าที่ใส่จำนวนติดลบ ถูกข้ามและยอดเป็น 0.0"""
    items = [("Book", -5, 100.0)]
    result = calc(items)
    assert result == 0.0


def test_pricing_mixed_zero_and_valid_quantity():
    """สินค้ามีทั้งจำนวน 0 และจำนวนปกติ"""
    items = [("Book", 0, 100.0), ("Pen", 1, 100.0)]
    result = calc(items)
    assert result == 107.0


# =====================================================================
# 4. กลุ่มสมาชิก (Member Discounts & Points)
# =====================================================================
def test_pricing_member_discount_and_points():
    """สมาชิกลด 5% และได้แต้มสะสม 1 แต้มต่อ 100 บาท"""
    items = [("Book", 2, 100.0)]
    result = calc(items, member="alice")
    assert result == 203.3
    assert member_points["alice"] == 1


def test_pricing_member_points_accumulation():
    """ทดสอบการสะสมแต้มต่อเนื่องของสมาชิกเมื่อเรียกซ้ำ"""
    items = [("Book", 2, 100.0)]
    calc(items, member="alice")
    calc(items, member="alice")
    assert member_points["alice"] == 2


# =====================================================================
# 5. กลุ่มคูปอง (Coupons)
# =====================================================================
def test_pricing_coupon_save50():
    """คูปอง SAVE50 ลด 50 บาท"""
    items = [("Book", 2, 100.0)]
    result = calc(items, coupon="SAVE50")
    assert result == 160.5


def test_pricing_coupon_half():
    """คูปอง HALF ลด 50%"""
    items = [("Book", 2, 100.0)]
    result = calc(items, coupon="HALF")
    assert result == 107.0


def test_pricing_coupon_newyear_in_january():
    """คูปอง NEWYEAR ใช้ในเดือนมกราคม ลด 20%"""
    items = [("Book", 2, 100.0)]
    january_date = datetime.date(2026, 1, 15)
    result = calc(items, coupon="NEWYEAR", today=january_date)
    assert result == 171.2


def test_pricing_coupon_newyear_outside_january():
    """คูปอง NEWYEAR ใช้นอกเดือนมกราคม ไม่ได้ส่วนลด"""
    items = [("Book", 2, 100.0)]
    february_date = datetime.date(2026, 2, 15)
    result = calc(items, coupon="NEWYEAR", today=february_date)
    assert result == 214.0


# =====================================================================
# 6. กลุ่มยอดติดลบ (Negative Subtotal Clamping)
# =====================================================================
def test_pricing_negative_subtotal_clamped_to_zero():
    """กรณีส่วนลดมากกว่าราคาสินค้า ยอดต้องถูกตัดเหลือ 0 ไม่ติดลบ"""
    items = [("Pencil", 1, 20.0)]
    result = calc(items, coupon="SAVE50")
    assert result == 0.0


# =====================================================================
# 7. กลุ่มค่าที่ฟังก์ชันเก็บไว้ (Side Effects / Saved State)
# =====================================================================
def test_pricing_saved_log_and_points():
    """ตรวจสอบประวัติ LOG และแต้มที่ฟังก์ชันบันทึกไว้ในทุก Transaction"""
    items = [("Notebook", 3, 50.0)]
    result = calc(items, member="bob")
    assert result == 152.47
    assert member_points["bob"] == 1
    assert LOG == [("bob", 152.47)]
