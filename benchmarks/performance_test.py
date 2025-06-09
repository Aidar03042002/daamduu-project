import time
import statistics
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import MenuItem, Payment
from django.core.cache import cache

User = get_user_model()

class PerformanceBenchmarks(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test menu items
        self.menu_items = [
            MenuItem.objects.create(
                name=f'Test Item {i}',
                description=f'Test Description {i}',
                price=10.00,
                image=f'test_image_{i}.jpg'
            ) for i in range(10)
        ]
        
        # Create test payments
        self.payments = [
            Payment.objects.create(
                user=self.user,
                item=self.menu_items[0],
                amount=10.00,
                status='completed'
            ) for _ in range(5)
        ]
        
        # Clear cache before each test
        cache.clear()
    
    def measure_time(self, func, *args, **kwargs):
        times = []
        for _ in range(10):  # Run 10 times for each test
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            times.append(end_time - start_time)
        return {
            'min': min(times),
            'max': max(times),
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def test_menu_list_performance(self):
        """Test performance of menu list endpoint"""
        results = self.measure_time(
            self.client.get,
            reverse('menu-list-create')
        )
        print("\nMenu List Performance:")
        print(f"Min: {results['min']:.4f}s")
        print(f"Max: {results['max']:.4f}s")
        print(f"Mean: {results['mean']:.4f}s")
        print(f"Median: {results['median']:.4f}s")
        print(f"Std Dev: {results['std_dev']:.4f}s")
    
    def test_menu_create_performance(self):
        """Test performance of menu creation endpoint"""
        data = {
            'name': 'New Test Item',
            'description': 'New Test Description',
            'price': 15.00,
            'image': 'new_test_image.jpg'
        }
        results = self.measure_time(
            self.client.post,
            reverse('menu-list-create'),
            data=data
        )
        print("\nMenu Create Performance:")
        print(f"Min: {results['min']:.4f}s")
        print(f"Max: {results['max']:.4f}s")
        print(f"Mean: {results['mean']:.4f}s")
        print(f"Median: {results['median']:.4f}s")
        print(f"Std Dev: {results['std_dev']:.4f}s")
    
    def test_payment_creation_performance(self):
        """Test performance of payment creation"""
        data = {
            'item_id': self.menu_items[0].id
        }
        results = self.measure_time(
            self.client.post,
            reverse('create-checkout-session'),
            data=data
        )
        print("\nPayment Creation Performance:")
        print(f"Min: {results['min']:.4f}s")
        print(f"Max: {results['max']:.4f}s")
        print(f"Mean: {results['mean']:.4f}s")
        print(f"Median: {results['median']:.4f}s")
        print(f"Std Dev: {results['std_dev']:.4f}s")
    
    def test_qr_generation_performance(self):
        """Test performance of QR code generation"""
        results = self.measure_time(
            self.client.get,
            reverse('scan')
        )
        print("\nQR Generation Performance:")
        print(f"Min: {results['min']:.4f}s")
        print(f"Max: {results['max']:.4f}s")
        print(f"Mean: {results['mean']:.4f}s")
        print(f"Median: {results['median']:.4f}s")
        print(f"Std Dev: {results['std_dev']:.4f}s")
    
    def test_cache_performance(self):
        """Test performance with and without cache"""
        # Test without cache
        cache.clear()
        no_cache_results = self.measure_time(
            self.client.get,
            reverse('menu-list-create')
        )
        
        # Test with cache
        self.client.get(reverse('menu-list-create'))  # Prime cache
        with_cache_results = self.measure_time(
            self.client.get,
            reverse('menu-list-create')
        )
        
        print("\nCache Performance Comparison:")
        print("Without Cache:")
        print(f"Mean: {no_cache_results['mean']:.4f}s")
        print("With Cache:")
        print(f"Mean: {with_cache_results['mean']:.4f}s")
        print(f"Improvement: {(no_cache_results['mean'] - with_cache_results['mean']) / no_cache_results['mean'] * 100:.2f}%") 