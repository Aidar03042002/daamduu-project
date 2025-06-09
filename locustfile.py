from locust import HttpUser, task, between
import random

class DaamduuUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login at the start of each user session
        self.client.post("/login/", {
            "username": "testuser",
            "password": "testpass123"
        })
    
    @task(3)
    def view_menu(self):
        # View menu items (high frequency)
        self.client.get("/api/menu/")
    
    @task(2)
    def view_weekly_menu(self):
        # View weekly menu
        self.client.get("/haftalik-menu/")
    
    @task(1)
    def make_payment(self):
        # Simulate payment process
        menu_items = self.client.get("/api/menu/").json()
        if menu_items:
            item = random.choice(menu_items)
            self.client.post("/create-checkout-session/", {
                "item_id": item["id"]
            })
    
    @task(1)
    def scan_qr(self):
        # Simulate QR code scanning
        self.client.get("/scan/")
    
    @task(1)
    def view_profile(self):
        # View user profile
        self.client.get("/profile/") 