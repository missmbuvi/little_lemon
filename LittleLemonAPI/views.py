from django.shortcuts import render

# Create your views here.
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer
from .permissions import IsManager, IsDeliveryCrew, IsCustomer
from django.http import JsonResponse

def index(request):
    return JsonResponse({"message": "Hello from LittleLemonAPI!"})

# Category Views
class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

# Menu Item Views
class MenuItemView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price']
    filterset_fields = ['category', 'featured']
    search_fields = ['title']
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManager()]

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManager()]

# Cart Views
class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsCustomer]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        unit_price = menuitem.price
        price = quantity * unit_price
        serializer.save(user=self.request.user, unit_price=unit_price, price=price)
    
    def delete(self, request, *args, **kwargs):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Order Views
class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=user)
        else:
            return Order.objects.filter(user=user)
    
    def perform_create(self, serializer):
        cart_items = Cart.objects.filter(user=self.request.user)
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        total = sum(item.price for item in cart_items)
        order = serializer.save(user=self.request.user, total=total)
        
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=cart_item.menuitem,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price
            )
        
        cart_items.delete()

class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=user)
        else:
            return Order.objects.filter(user=user)

# Manager Group Management
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated, IsManager])
def managers(request):
    if request.method == 'POST':
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, username=username)
        managers_group = Group.objects.get(name='Manager')
        managers_group.user_set.add(user)
        
        return Response({'message': f'User {username} added to Manager group'}, status=status.HTTP_201_CREATED)
    
    elif request.method == 'GET':
        managers_group = Group.objects.get(name='Manager')
        managers = managers_group.user_set.all()
        return Response({'managers': [user.username for user in managers]})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsManager])
def manager_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    managers_group = Group.objects.get(name='Manager')
    managers_group.user_set.remove(user)
    
    return Response({'message': f'User {user.username} removed from Manager group'}, status=status.HTTP_200_OK)

# Delivery Crew Management
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated, IsManager])
def delivery_crew(request):
    if request.method == 'POST':
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, username=username)
        delivery_group = Group.objects.get(name='Delivery Crew')
        delivery_group.user_set.add(user)
        
        return Response({'message': f'User {username} added to Delivery Crew group'}, status=status.HTTP_201_CREATED)
    
    elif request.method == 'GET':
        delivery_group = Group.objects.get(name='Delivery Crew')
        delivery_crew = delivery_group.user_set.all()
        return Response({'delivery_crew': [user.username for user in delivery_crew]})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsManager])
def delivery_crew_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    delivery_group = Group.objects.get(name='Delivery Crew')
    delivery_group.user_set.remove(user)
    
    return Response({'message': f'User {user.username} removed from Delivery Crew group'}, status=status.HTTP_200_OK)