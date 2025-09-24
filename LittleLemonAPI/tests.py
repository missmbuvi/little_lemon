from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Group
from rest_framework import status
from .models import Category, MenuItem, Cart, Order

class LittleLemonAPITests(TestCase):
    def setUp(self):
        # Create groups
        self.manager_group, _ = Group.objects.get_or_create(name='Manager')
        self.delivery_group, _ = Group.objects.get_or_create(name='Delivery Crew')

        # Create users
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'password123')
        self.manager = User.objects.create_user('manager', 'manager@test.com', 'password123')
        self.customer = User.objects.create_user('customer', 'customer@test.com', 'password123')
        self.delivery = User.objects.create_user('delivery', 'delivery@test.com', 'password123')

        # Add manager to manager group
        self.manager.groups.add(self.manager_group)

        # API client
        self.client = APIClient()

    # -------------------- Admin Tests -------------------- #
    def test_admin_can_add_category(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/categories/', {'slug': 'drinks', 'title': 'Drinks'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_add_menu_item(self):
        self.client.force_authenticate(user=self.admin)
        category = Category.objects.create(slug='main-course', title='Main Course')
        response = self.client.post('/api/menu-items/', {
            'title': 'Pizza',
            'price': '15.00',
            'featured': False,
            'category_id': category.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_assign_manager(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/managers/', {'username': 'delivery'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.delivery.groups.filter(name='Manager').exists())

    # -------------------- Manager Tests -------------------- #
    def test_manager_login(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/menu-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manager_can_update_item_of_the_day(self):
        self.client.force_authenticate(user=self.manager)
        category = Category.objects.create(slug='special', title='Specials')
        item = MenuItem.objects.create(title='Burger', price='10.00', featured=False, category=category)
        response = self.client.patch(f'/api/menu-items/{item.id}/', {'featured': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertTrue(item.featured)

    def test_manager_can_assign_delivery_crew(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/delivery-crew/', {'username': 'customer'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.customer.groups.filter(name='Delivery Crew').exists())

    # -------------------- Customer Tests -------------------- #
    def test_customer_can_register_and_login(self):
        response = self.client.post('/api/users/register/', {
            'username': 'newcustomer',
            'password': 'pass123',
            'email': 'new@test.com'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='newcustomer')
        self.assertIsNotNone(user)

    def test_customer_can_browse_categories_and_menuitems(self):
        self.client.force_authenticate(user=self.customer)
        category = Category.objects.create(slug='dessert', title='Dessert')
        MenuItem.objects.create(title='Cake', price='5.00', featured=False, category=category)
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response2 = self.client.get('/api/menu-items/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_customer_can_filter_paginate_sort_menuitems(self):
        self.client.force_authenticate(user=self.customer)
        category = Category.objects.create(slug='drinks', title='Drinks')
        for i in range(5):
            MenuItem.objects.create(title=f'Drink{i}', price=5+i, featured=False, category=category)
        # By category
        response = self.client.get(f'/api/menu-items/?category={category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Pagination
        response = self.client.get('/api/menu-items/?page=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Sorting
        response = self.client.get('/api/menu-items/?ordering=price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_can_add_to_cart_and_view_cart(self):
        self.client.force_authenticate(user=self.customer)
        category = Category.objects.create(slug='snacks', title='Snacks')
        item = MenuItem.objects.create(title='Chips', price='3.00', featured=False, category=category)
        response = self.client.post('/api/cart/', {'menuitem_id': item.id, 'quantity': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response2 = self.client.get('/api/cart/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data), 1)

    def test_customer_can_place_order_and_view_orders(self):
        self.client.force_authenticate(user=self.customer)
        category = Category.objects.create(slug='snacks', title='Snacks')
        item = MenuItem.objects.create(title='Chips', price='3.00', featured=False, category=category)
        # Add to cart
        self.client.post('/api/cart/', {'menuitem_id': item.id, 'quantity': 2}, format='json')
        # Place order
        response = self.client.post('/api/orders/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # View own orders
        response2 = self.client.get('/api/orders/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data), 1)

    # -------------------- Delivery Crew Tests -------------------- #
    def test_delivery_can_access_assigned_orders_and_update_status(self):
        self.client.force_authenticate(user=self.customer)
        category = Category.objects.create(slug='snacks', title='Snacks')
        item = MenuItem.objects.create(title='Chips', price='3.00', featured=False, category=category)
        # Add to cart and place order
        self.client.post('/api/cart/', {'menuitem_id': item.id, 'quantity': 2}, format='json')
        response = self.client.post('/api/orders/', {}, format='json')
        order_id = response.data['id']

        # Assign delivery crew
        self.client.force_authenticate(user=self.manager)
        self.client.patch(f'/api/orders/{order_id}/', {'delivery_crew': self.delivery.id}, format='json')

        # Delivery crew updates status
        self.client.force_authenticate(user=self.delivery)
        response = self.client.patch(f'/api/orders/{order_id}/', {'status': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
