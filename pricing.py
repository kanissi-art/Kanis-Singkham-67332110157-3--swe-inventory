"""โมดูลคำนวณราคาและส่วนลดของระบบ Inventory (ฉบับ Refactored).

ปรับปรุงให้อ่านง่าย มีโครงสร้างชัดเจน แยกฟังก์ชันตามความรับผิดชอบ (Single Responsibility Principle)
โดยยังคงรักษาพฤติกรรม สูตรคำนวณ ลำดับส่วนลด และการปัดเศษเดิมไว้ 100%
"""

from __future__ import annotations

import datetime
from collections.abc import Sequence

# =====================================================================
# ค่าคงที่อัตราภาษีและส่วนลด (Business Constants)
# =====================================================================
TAX: float = 0.07

# เกณฑ์ส่วนลดตามปริมาณการสั่งซื้อ (Bulk Discounts)
BULK_TIER_LARGE_QTY: int = 100
BULK_DISCOUNT_LARGE_RATE: float = 0.90  # ลด 10%
BULK_TIER_MEDIUM_QTY: int = 50
BULK_DISCOUNT_MEDIUM_RATE: float = 0.95  # ลด 5%

# ส่วนลดและแต้มสมาชิก (Member Benefits)
MEMBER_DISCOUNT_RATE: float = 0.95  # ลด 5%
MEMBER_SPEND_PER_POINT: int = 100  # สะสม 1 แต้มต่อ 100 บาท

# รหัสคูปองส่วนลด (Coupon Codes)
COUPON_SAVE50: str = "SAVE50"
COUPON_SAVE50_AMOUNT: float = 50.0

COUPON_HALF: str = "HALF"
COUPON_HALF_RATE: float = 0.5  # ลด 50%

COUPON_NEWYEAR: str = "NEWYEAR"
COUPON_NEWYEAR_RATE: float = 0.8  # ลด 20%
NEWYEAR_ACTIVE_MONTH: int = 1  # ใช้ได้เฉพาะเดือนมกราคม

# สถานะตัวแปรส่วนกลาง (Shared State สำหรับ backward compatibility)
member_points: dict[str, int] = {}
LOG: list[tuple[str | None, float]] = []

ItemTuple = tuple[str, int, float] | tuple[str, int, int]


# =====================================================================
# ฟังก์ชันย่อยแยกตามหน้าที่ (Single Responsibility Helpers)
# =====================================================================

def calculate_items_subtotal(items: Sequence[ItemTuple]) -> float:
    """คำนวณยอดรวมของสินค้าทั้งหมด พร้อมคิดส่วนลดตามปริมาณการสั่งซื้อ (Bulk Discount)."""
    running_subtotal: float = 0.0
    for item in items:
        _item_name, quantity, unit_price = item[0], item[1], item[2]
        if quantity <= 0:
            continue

        item_total = quantity * unit_price
        if quantity >= BULK_TIER_LARGE_QTY:
            item_total *= BULK_DISCOUNT_LARGE_RATE
        elif quantity >= BULK_TIER_MEDIUM_QTY:
            item_total *= BULK_DISCOUNT_MEDIUM_RATE

        running_subtotal += item_total

    return running_subtotal


def apply_member_benefits(subtotal: float, member: str | None) -> float:
    """คำนวณส่วนลดสมาชิก 5% และสะสมแต้ม 1 แต้มต่อยอดใช้จ่าย 100 บาท."""
    if member is None:
        return subtotal

    if member not in member_points:
        member_points[member] = 0

    discounted_subtotal = subtotal * MEMBER_DISCOUNT_RATE
    earned_points = int(discounted_subtotal / MEMBER_SPEND_PER_POINT)
    member_points[member] += earned_points

    return discounted_subtotal


def apply_coupon_discount(
    subtotal: float,
    coupon: str | None,
    today: datetime.date | None = None,
) -> float:
    """ประมวลผลคูปองส่วนลดตามเงื่อนไขที่กำหนด."""
    if coupon is None:
        return subtotal

    if coupon == COUPON_SAVE50:
        return subtotal - COUPON_SAVE50_AMOUNT

    if coupon == COUPON_HALF:
        return subtotal * COUPON_HALF_RATE

    if coupon == COUPON_NEWYEAR:
        current_date = datetime.date.today() if today is None else today
        if current_date.month == NEWYEAR_ACTIVE_MONTH:
            return subtotal * COUPON_NEWYEAR_RATE

    return subtotal


def apply_tax_and_rounding(amount: float) -> float:
    """ป้องกันยอดติดลบ คำนวณภาษีมูลค่าเพิ่ม และปัดเศษทศนิยม 2 ตำแหน่ง."""
    clamped_amount = max(0.0, amount)
    amount_with_tax = clamped_amount + (clamped_amount * TAX)
    return round(amount_with_tax, 2)


# =====================================================================
# ฟังก์ชันหลัก (Main Calculation Entrypoint)
# =====================================================================

def calc(
    items: Sequence[ItemTuple],
    member: str | None = None,
    coupon: str | None = None,
    today: datetime.date | None = None,
) -> float:
    """คำนวณราคาสุทธิของสินค้าในตะกร้าตามลำดับสิทธิประโยชน์ที่กำหนด."""
    subtotal = calculate_items_subtotal(items)
    subtotal = apply_member_benefits(subtotal, member)
    subtotal = apply_coupon_discount(subtotal, coupon, today)
    final_price = apply_tax_and_rounding(subtotal)

    LOG.append((member, final_price))
    return final_price
