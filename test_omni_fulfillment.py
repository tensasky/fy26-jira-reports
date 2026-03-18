#!/usr/bin/env python3
"""
Omni Fulfillment Dataflow 自动化测试脚本
Generated from: https://lululemon.atlassian.net/wiki/spaces/CNT/pages/4519265948

业务流程覆盖:
1. Online order, ship from DC
2. Online order, ship from Store (SFS)
3. Online order, return to DC
4. Online presale order, pack after deposit
5. Online order, exchange from DC
6. Order cancellation before shipment
7. Backorder - Courier Order Create Failed
8. B2B Order flows
9. Interception Order - Refund Only
10. EC Order Shortage process
"""

import unittest
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

# ============ 配置 ============
BASE_URL = "https://api.omni-fulfillment.lululemon.com"  # 请替换为实际 API 地址
API_KEY = "your_api_key_here"  # 请替换为实际 API Key
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    "X-Request-ID": ""
}


class OmniFulfillmentTestBase(unittest.TestCase):
    """测试基类"""
    
    @classmethod
    def setUpClass(cls):
        cls.base_url = BASE_URL
        cls.headers = HEADERS.copy()
        cls.test_data = {}
    
    def generate_request_id(self) -> str:
        """生成唯一请求 ID"""
        return f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(self)}"
    
    def make_request(self, method: str, endpoint: str, payload: Dict = None) -> Dict:
        """通用请求方法"""
        url = f"{self.base_url}{endpoint}"
        self.headers["X-Request-ID"] = self.generate_request_id()
        
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        self.assertIn(response.status_code, [200, 201, 202], 
                     f"Request failed: {response.text}")
        return response.json()


class TestOnlineOrderShipFromDC(OmniFulfillmentTestBase):
    """
    3PL Integration scenario: #1
    Happy Path - DC - All products are shipped from DC-EC
    """
    
    def test_01_create_online_order(self):
        """测试创建线上订单 (Ship from DC)"""
        payload = {
            "order_type": "ONLINE",
            "fulfillment_type": "SHIP_FROM_DC",
            "customer": {
                "customer_id": "CUST001",
                "email": "test@example.com",
                "phone": "+86-138-0013-8000"
            },
            "shipping_address": {
                "name": "Test User",
                "address_line1": "123 Test Street",
                "city": "Shanghai",
                "country": "CN",
                "postal_code": "200000"
            },
            "items": [
                {
                    "sku": "SKU001",
                    "quantity": 2,
                    "unit_price": 850.00
                }
            ],
            "payment": {
                "method": "ALIPAY",
                "amount": 1700.00
            }
        }
        
        result = self.make_request("POST", "/v1/orders", payload)
        self.assertIsNotNone(result.get("order_id"))
        self.assertEqual(result.get("status"), "CREATED")
        
        # 保存订单 ID 供后续测试使用
        self.__class__.test_order_id = result["order_id"]
        print(f"✓ Order created: {result['order_id']}")
    
    def test_02_submit_to_dc(self):
        """测试订单下发到 DC"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            self.skipTest("No order created in previous test")
        
        payload = {"action": "SUBMIT_TO_DC"}
        result = self.make_request("POST", f"/v1/orders/{order_id}/action", payload)
        
        self.assertEqual(result.get("fulfillment_status"), "SENT_TO_DC")
        print(f"✓ Order {order_id} submitted to DC")
    
    def test_03_dc_confirm_pick(self):
        """测试 DC 拣货确认"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            self.skipTest("No order created")
        
        payload = {
            "dc_id": "DC001",
            "picked_items": [
                {"sku": "SKU001", "picked_qty": 2}
            ],
            "picker_id": "EMP001"
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/dc/pick", payload)
        
        self.assertEqual(result.get("status"), "PICKED")
        print(f"✓ DC pick confirmed for order {order_id}")
    
    def test_04_dc_confirm_pack(self):
        """测试 DC 打包确认"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            self.skipTest("No order created")
        
        payload = {
            "package_id": f"PKG-{order_id}",
            "weight": 0.5,
            "dimensions": {"length": 30, "width": 20, "height": 10}
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/dc/pack", payload)
        
        self.assertEqual(result.get("status"), "PACKED")
        print(f"✓ DC pack confirmed for order {order_id}")
    
    def test_05_create_courier_order(self):
        """测试创建物流订单"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            self.skipTest("No order created")
        
        payload = {
            "courier_code": "SF",
            "service_type": "STANDARD",
            "package_id": f"PKG-{order_id}"
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/shipment", payload)
        
        self.assertIsNotNone(result.get("tracking_number"))
        self.__class__.tracking_number = result["tracking_number"]
        print(f"✓ Courier order created, tracking: {result['tracking_number']}")
    
    def test_06_confirm_shipment(self):
        """测试确认发货"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            self.skipTest("No order created")
        
        payload = {
            "tracking_number": getattr(self.__class__, 'tracking_number', 'TN123'),
            "shipped_at": datetime.now().isoformat()
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/ship", payload)
        
        self.assertEqual(result.get("status"), "SHIPPED")
        print(f"✓ Order {order_id} shipped")


class TestOnlineOrderShipFromStore(OmniFulfillmentTestBase):
    """
    SFS (Ship From Store) 流程测试
    """
    
    def test_01_create_sfs_order(self):
        """测试创建 SFS 订单"""
        payload = {
            "order_type": "ONLINE",
            "fulfillment_type": "SHIP_FROM_STORE",
            "items": [
                {
                    "sku": "SKU002",
                    "quantity": 1,
                    "preferred_store": "STORE001"
                }
            ]
        }
        
        result = self.make_request("POST", "/v1/orders", payload)
        self.assertEqual(result.get("fulfillment_type"), "SHIP_FROM_STORE")
        self.__class__.sfs_order_id = result["order_id"]
        print(f"✓ SFS Order created: {result['order_id']}")
    
    def test_02_store_accept(self):
        """测试门店接单"""
        order_id = getattr(self.__class__, 'sfs_order_id', None)
        if not order_id:
            self.skipTest("No SFS order created")
        
        payload = {
            "store_id": "STORE001",
            "action": "ACCEPT",
            "accepted_by": "STAFF001"
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/store/action", payload)
        
        self.assertEqual(result.get("store_status"), "ACCEPTED")
        print(f"✓ Store accepted order {order_id}")
    
    def test_03_store_pick_and_pack(self):
        """测试门店拣货打包"""
        order_id = getattr(self.__class__, 'sfs_order_id', None)
        if not order_id:
            self.skipTest("No SFS order created")
        
        payload = {
            "store_id": "STORE001",
            "picked_items": [{"sku": "SKU002", "qty": 1}],
            "package_id": f"SFS-{order_id}"
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/store/fulfill", payload)
        
        self.assertEqual(result.get("status"), "READY_FOR_PICKUP")
        print(f"✓ Store pick & pack completed for order {order_id}")


class TestOnlineOrderReturnToDC(OmniFulfillmentTestBase):
    """
    3PL Integration: #6 #7 #8 - Refund & return
    Online order, return to DC
    """
    
    def test_01_initiate_return(self):
        """测试发起退货"""
        # 模拟一个已完成的订单
        original_order_id = "ORD12345"
        
        payload = {
            "original_order_id": original_order_id,
            "return_type": "RETURN_TO_DC",
            "items": [
                {
                    "sku": "SKU001",
                    "return_qty": 1,
                    "reason": "SIZE_ISSUE"
                }
            ],
            "refund_method": "ORIGINAL_PAYMENT"
        }
        
        result = self.make_request("POST", "/v1/returns", payload)
        self.assertIsNotNone(result.get("return_order_id"))
        self.__class__.return_order_id = result["return_order_id"]
        print(f"✓ Return initiated: {result['return_order_id']}")
    
    def test_02_create_return_label(self):
        """测试创建退货物流标签"""
        return_id = getattr(self.__class__, 'return_order_id', None)
        if not return_id:
            self.skipTest("No return order created")
        
        payload = {
            "courier_code": "SF",
            "pickup_address": {
                "name": "Customer Name",
                "phone": "+86-138-0013-8000",
                "address": "Customer Address"
            }
        }
        result = self.make_request("POST", f"/v1/returns/{return_id}/label", payload)
        
        self.assertIsNotNone(result.get("return_tracking_number"))
        print(f"✓ Return label created: {result['return_tracking_number']}")
    
    def test_03_dc_receive_return(self):
        """测试 DC 收货确认"""
        return_id = getattr(self.__class__, 'return_order_id', None)
        if not return_id:
            self.skipTest("No return order created")
        
        payload = {
            "dc_id": "DC001",
            "received_items": [
                {"sku": "SKU001", "received_qty": 1, "condition": "GOOD"}
            ],
            "received_by": "EMP001",
            "received_at": datetime.now().isoformat()
        }
        result = self.make_request("POST", f"/v1/returns/{return_id}/receive", payload)
        
        self.assertEqual(result.get("status"), "RECEIVED_AT_DC")
        print(f"✓ Return received at DC: {return_id}")
    
    def test_04_process_refund(self):
        """测试处理退款"""
        return_id = getattr(self.__class__, 'return_order_id', None)
        if not return_id:
            self.skipTest("No return order created")
        
        payload = {
            "refund_amount": 850.00,
            "refund_method": "ORIGINAL_PAYMENT",
            "processed_by": "SYSTEM"
        }
        result = self.make_request("POST", f"/v1/returns/{return_id}/refund", payload)
        
        self.assertEqual(result.get("refund_status"), "COMPLETED")
        print(f"✓ Refund processed for return: {return_id}")


class TestPresaleOrder(OmniFulfillmentTestBase):
    """
    3PL Integration: #2 - Pre sales
    Online presale order, pack after deposit
    """
    
    def test_01_create_presale_order(self):
        """测试创建预售订单"""
        payload = {
            "order_type": "ONLINE_PRESALE",
            "fulfillment_type": "SHIP_FROM_DC",
            "presale_config": {
                "deposit_ratio": 0.2,
                "deposit_due_date": "2026-03-15T23:59:59Z",
                "final_payment_due_date": "2026-03-20T23:59:59Z"
            },
            "items": [
                {
                    "sku": "NEW_SKU_001",
                    "quantity": 1,
                    "presale_price": 1200.00
                }
            ]
        }
        
        result = self.make_request("POST", "/v1/orders/presale", payload)
        self.assertEqual(result.get("order_type"), "ONLINE_PRESALE")
        self.__class__.presale_order_id = result["order_id"]
        print(f"✓ Presale order created: {result['order_id']}")
    
    def test_02_pay_deposit(self):
        """测试支付定金"""
        order_id = getattr(self.__class__, 'presale_order_id', None)
        if not order_id:
            self.skipTest("No presale order created")
        
        payload = {
            "payment_type": "DEPOSIT",
            "amount": 240.00,  # 20% of 1200
            "payment_method": "WECHAT_PAY"
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/payment", payload)
        
        self.assertEqual(result.get("deposit_status"), "PAID")
        print(f"✓ Deposit paid for order: {order_id}")
    
    def test_03_pay_final_payment(self):
        """测试支付尾款"""
        order_id = getattr(self.__class__, 'presale_order_id', None)
        if not order_id:
            self.skipTest("No presale order created")
        
        payload = {
            "payment_type": "FINAL_PAYMENT",
            "amount": 960.00,  # 80% of 1200
            "payment_method": "WECHAT_PAY"
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/payment", payload)
        
        self.assertEqual(result.get("payment_status"), "FULLY_PAID")
        print(f"✓ Final payment completed for order: {order_id}")
    
    def test_04_dc_pack_after_deposit(self):
        """测试定金后 DC 打包"""
        order_id = getattr(self.__class__, 'presale_order_id', None)
        if not order_id:
            self.skipTest("No presale order created")
        
        payload = {
            "dc_id": "DC001",
            "pack_after": "DEPOSIT",  # Pack after deposit received
            "items": [{"sku": "NEW_SKU_001", "qty": 1}]
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/dc/presale-pack", payload)
        
        self.assertEqual(result.get("presale_status"), "PACKED_AFTER_DEPOSIT")
        print(f"✓ Packed after deposit for order: {order_id}")


class TestOrderExchange(OmniFulfillmentTestBase):
    """
    3PL Integration: #10 - Exchange
    Online order shipped from DC/store, exchange from DC
    """
    
    def test_01_initiate_exchange(self):
        """测试发起换货"""
        original_order_id = "ORD12345"
        
        payload = {
            "original_order_id": original_order_id,
            "exchange_type": "EXCHANGE_FROM_DC",
            "original_items": [
                {"sku": "SKU001", "qty": 1}
            ],
            "new_items": [
                {"sku": "SKU001-BLUE", "qty": 1, "size": "M"}  # 换颜色和/或尺码
            ],
            "reason": "COLOR_CHANGE"
        }
        
        result = self.make_request("POST", "/v1/exchanges", payload)
        self.assertIsNotNone(result.get("exchange_order_id"))
        self.__class__.exchange_id = result["exchange_order_id"]
        print(f"✓ Exchange initiated: {result['exchange_order_id']}")
    
    def test_02_receive_original_items(self):
        """测试 DC 接收原商品"""
        exchange_id = getattr(self.__class__, 'exchange_id', None)
        if not exchange_id:
            self.skipTest("No exchange order created")
        
        payload = {
            "dc_id": "DC001",
            "received_items": [{"sku": "SKU001", "qty": 1, "condition": "GOOD"}],
            "received_at": datetime.now().isoformat()
        }
        result = self.make_request("POST", f"/v1/exchanges/{exchange_id}/receive", payload)
        
        self.assertEqual(result.get("status"), "ORIGINAL_RECEIVED")
        print(f"✓ Original items received for exchange: {exchange_id}")
    
    def test_03_ship_exchange_items(self):
        """测试发出换货商品"""
        exchange_id = getattr(self.__class__, 'exchange_id', None)
        if not exchange_id:
            self.skipTest("No exchange order created")
        
        payload = {
            "dc_id": "DC001",
            "shipped_items": [{"sku": "SKU001-BLUE", "qty": 1}],
            "courier_code": "SF",
            "tracking_number": f"SF{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        result = self.make_request("POST", f"/v1/exchanges/{exchange_id}/ship", payload)
        
        self.assertEqual(result.get("status"), "EXCHANGE_SHIPPED")
        print(f"✓ Exchange items shipped: {exchange_id}")


class TestOrderCancellation(OmniFulfillmentTestBase):
    """
    3PL Integration: #5.1, #5.2 - Refund - Inflight Cancellation
    Order cancellation before shipment (full)
    """
    
    def test_01_cancel_before_fulfillment(self):
        """测试发货前取消订单"""
        # 创建新订单
        create_payload = {
            "order_type": "ONLINE",
            "fulfillment_type": "SHIP_FROM_DC",
            "items": [{"sku": "SKU003", "quantity": 1}]
        }
        order_result = self.make_request("POST", "/v1/orders", create_payload)
        order_id = order_result["order_id"]
        
        # 立即取消（在发货前）
        payload = {
            "reason": "CUSTOMER_REQUEST",
            "cancelled_by": "CUSTOMER",
            "refund_required": True
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/cancel", payload)
        
        self.assertEqual(result.get("status"), "CANCELLED")
        self.assertEqual(result.get("refund_status"), "INITIATED")
        print(f"✓ Order cancelled before fulfillment: {order_id}")
    
    def test_02_cancel_after_fulfillment_sent(self):
        """测试已下发 DC 后的取消（拦截）"""
        # 模拟已下发到 DC 的订单
        order_id = "ORD-IN-PROGRESS"
        
        payload = {
            "reason": "CUSTOMER_REQUEST",
            "cancelled_by": "CUSTOMER",
            "interception_required": True  # 需要拦截
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/cancel", payload)
        
        # 状态应为拦截中
        self.assertIn(result.get("status"), ["CANCELLATION_REQUESTED", "INTERCEPTING"])
        print(f"✓ Cancellation requested after fulfillment sent: {order_id}")


class TestBackorderScenario(OmniFulfillmentTestBase):
    """
    3PL Integration: #4 - Backorder - Courier Order Create Failed
    """
    
    def test_01_courier_order_create_failed(self):
        """测试物流订单创建失败后的回退处理"""
        order_id = "ORD-FOR-BACKORDER"
        
        # 模拟创建物流订单失败
        payload = {
            "courier_code": "SF",
            "simulate_failure": True  # 测试用参数
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/shipment/retry", payload)
        
        self.assertEqual(result.get("backorder_status"), "BACKORDER_CREATED")
        self.__class__.backorder_id = result.get("backorder_id")
        print(f"✓ Backorder created: {result.get('backorder_id')}")
    
    def test_02_retry_courier_order(self):
        """测试重新创建物流订单"""
        order_id = "ORD-FOR-BACKORDER"
        
        payload = {
            "backorder_id": getattr(self.__class__, 'backorder_id', 'BO001'),
            "courier_code": "SF",  # 或更换其他物流
            "retry_attempt": 2
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/shipment/retry", payload)
        
        self.assertIn(result.get("status"), ["SHIPMENT_RETRY_SUCCESS", "BACKORDER_RESOLVED"])
        print(f"✓ Courier order retry successful for: {order_id}")


class TestB2BOrder(OmniFulfillmentTestBase):
    """
    B2B Order flows
    """
    
    def test_01_create_b2b_order(self):
        """测试创建 B2B 订单"""
        payload = {
            "order_type": "B2B",
            "customer": {
                "business_name": "Lululemon Store Shanghai",
                "business_id": "BIZ001",
                "store_code": "STORE001"
            },
            "items": [
                {
                    "sku": "BULK-SKU-001",
                    "quantity": 100,
                    "unit_price": 450.00
                }
            ],
            "delivery_date": "2026-03-15",
            "delivery_location": "STORE001"
        }
        
        result = self.make_request("POST", "/v1/b2b/orders", payload)
        self.assertIsNotNone(result.get("b2b_order_id"))
        self.__class__.b2b_order_id = result["b2b_order_id"]
        print(f"✓ B2B order created: {result['b2b_order_id']}")
    
    def test_02_b2b_exchange_to_dc(self):
        """测试 B2B 换货回 DC"""
        b2b_order_id = getattr(self.__class__, 'b2b_order_id', 'B2B001')
        
        payload = {
            "original_b2b_order_id": b2b_order_id,
            "exchange_items": [
                {"sku": "BULK-SKU-001", "return_qty": 20, "condition": "DAMAGED"}
            ],
            "exchange_to": "DC001"
        }
        result = self.make_request("POST", "/v1/b2b/exchanges", payload)
        
        self.assertIsNotNone(result.get("b2b_exchange_id"))
        print(f"✓ B2B exchange to DC created: {result['b2b_exchange_id']}")


class TestInterceptionOrder(OmniFulfillmentTestBase):
    """
    Interception Order - Refund Only
    """
    
    def test_intercept_and_refund_only(self):
        """测试拦截订单并仅退款"""
        # 模拟已发货的订单
        order_id = "ORD-SHIPPED-001"
        
        payload = {
            "interception_type": "REFUND_ONLY",
            "reason": "CUSTOMER_REQUEST",
            "refund_amount": 850.00,
            "courier_interception_requested": True
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/intercept", payload)
        
        self.assertEqual(result.get("interception_status"), "INTERCEPTING")
        self.assertEqual(result.get("refund_type"), "REFUND_ONLY")
        print(f"✓ Interception with refund only initiated: {order_id}")


class TestECOrderShortage(OmniFulfillmentTestBase):
    """
    EC Order Shortage process
    """
    
    def test_handle_inventory_shortage(self):
        """测试处理库存短缺"""
        order_id = "ORD-SHORTAGE-001"
        
        payload = {
            "shortage_items": [
                {"sku": "SKU001", "ordered_qty": 2, "available_qty": 1}
            ],
            "resolution_type": "PARTIAL_SHIP",  # 或 "BACKORDER", "CANCEL"
            "customer_notification_required": True
        }
        result = self.make_request("POST", f"/v1/orders/{order_id}/shortage", payload)
        
        self.assertEqual(result.get("shortage_status"), "RESOLVED")
        self.assertEqual(result.get("resolution_type"), "PARTIAL_SHIP")
        print(f"✓ Shortage handled for order: {order_id}")


# ============ 测试执行入口 ============
if __name__ == '__main__':
    # 配置测试
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    test_classes = [
        TestOnlineOrderShipFromDC,
        TestOnlineOrderShipFromStore,
        TestOnlineOrderReturnToDC,
        TestPresaleOrder,
        TestOrderExchange,
        TestOrderCancellation,
        TestBackorderScenario,
        TestB2BOrder,
        TestInterceptionOrder,
        TestECOrderShortage
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出汇总
    print("\n" + "="*60)
    print("测试执行完成!")
    print(f"总测试数: {result.testsRun}")
    print(f"通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*60)
