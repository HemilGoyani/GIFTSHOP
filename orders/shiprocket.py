import requests
from django.conf import settings
import json

class ShiprocketAPI:
    def __init__(self):
        self.base_url = settings.SHIPROCKET_API_URL
        self.token = self._get_token()

    def _get_token(self):
        """Get authentication token from Shiprocket"""
        url = f"{self.base_url}/external/auth/login"
        payload = {
            "email": settings.SHIPROCKET_EMAIL,
            "password": settings.SHIPROCKET_PASSWORD
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get('token')
        return None

    def create_order(self, order):
        """Create order in Shiprocket"""
        if not self.token:
            return None

        url = f"{self.base_url}/external/orders/create/adhoc"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        # Calculate order total including COD charges if applicable
        order_total = order.final_price if order.final_price else order.total_price

        # Prepare order items
        order_items = []
        for item in order.items.all():
            order_items.append({
                "name": item.product.name,
                "sku": item.product.code,
                "units": item.quantity,
                "selling_price": item.price,
                "discount": "",
                "tax": "",
                "hsn": ""
            })

        payload = {
            "order_id": order.order_number,
            "order_date": order.created_at.strftime("%Y-%m-%d"),
            "pickup_location": "Primary",
            "billing_customer_name": order.name,
            "billing_last_name": "",
            "billing_address": order.address,
            "billing_city": order.city,
            "billing_pincode": order.pincode,
            "billing_state": order.state,
            "billing_country": "India",
            "billing_email": order.email,
            "billing_phone": str(order.phone_number),
            "shipping_is_billing": True,
            "order_items": order_items,
            "payment_method": "COD" if order.payment_method == 'COD' else "Prepaid",
            "sub_total": order_total,
            "length": 10,
            "breadth": 10,
            "height": 10,
            "weight": 0.5,
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            return response.json()
        return None

    def generate_awb(self, shipment_id):
        """Generate AWB number for a shipment"""
        if not self.token:
            return None

        url = f"{self.base_url}/external/courier/assign/awb"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        payload = {
            "shipment_id": shipment_id,
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        return None

    def track_order(self, awb_code):
        """Track order using AWB number"""
        if not self.token:
            return None

        url = f"{self.base_url}/external/courier/track/awb/{awb_code}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None 