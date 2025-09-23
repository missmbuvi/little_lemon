from django.contrib.auth.models import Group

# Create the required groups
Group.objects.get_or_create(name='Manager')
Group.objects.get_or_create(name='Delivery Crew')
print("Groups created successfully!")