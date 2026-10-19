import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'juice_shop.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Category, Product

def seed():
    # Create admin user if not exists
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@juiceshop.com', 'admin123')
        print('Created admin user (admin / admin123)')

    # Create demo user
    if not User.objects.filter(username='demo').exists():
        User.objects.create_user('demo', 'demo@juiceshop.com', 'demo123')
        print('Created demo user (demo / demo123)')

    # Create categories
    categories = {
        'Fruit Juices': 'Freshly squeezed fruit juices made from organic fruits.',
        'Vegetable Juices': 'Nutrient-packed vegetable blends for a healthy boost.',
        'Smoothies': 'Creamy smoothies blended with fruits and yogurt.',
        'Detox Drinks': 'Cleansing detox beverages with superfood ingredients.',
        'Energy Boosters': 'Natural energy drinks to power your day.',
    }

    created_categories = {}
    for name, desc in categories.items():
        cat, created = Category.objects.get_or_create(
            name=name,
            defaults={
                'slug': name.lower().replace(' ', '-'),
                'description': desc,
            }
        )
        created_categories[name] = cat
        if created:
            print(f'Created category: {name}')

    # Create products
    products_data = [
        ('Orange Delight', 'Fruit Juices', 4.99, 'Freshly squeezed oranges with a hint of honey. A classic favorite packed with Vitamin C.', 50),
        ('Berry Blast', 'Fruit Juices', 5.99, 'A vibrant mix of strawberries, blueberries, and raspberries. Antioxidant rich and delicious.', 45),
        ('Green Goodness', 'Vegetable Juices', 5.49, 'Kale, spinach, cucumber, and green apple blended to perfection. A powerhouse of nutrients.', 40),
        ('Carrot Zing', 'Vegetable Juices', 4.49, 'Fresh carrot juice with a touch of ginger and lemon. Great for your immune system.', 35),
        ('Mango Tango', 'Smoothies', 6.49, 'Creamy mango smoothie with yogurt and a dash of cardamom. Tropical paradise in a cup.', 30),
        ('Banana Boost', 'Smoothies', 5.99, 'Rich banana smoothie with peanut butter and oats. Perfect post-workout refuel.', 25),
        ('Citrus Cleanse', 'Detox Drinks', 6.99, 'Lemon, lime, grapefruit, and a hint of cayenne. Kickstart your detox journey.', 20),
        ('Green Detox', 'Detox Drinks', 7.49, 'Wheatgrass, spirulina, aloe vera, and green tea. The ultimate cleansing blend.', 15),
        ('Electro Charge', 'Energy Boosters', 5.99, 'Coconut water, pomegranate, and electrolytes. Nature\'s sports drink.', 35),
        ('Protein Punch', 'Energy Boosters', 7.99, 'Almond milk, protein powder, banana, and dates. Fuel for your active lifestyle.', 20),
        ('Watermelon Chill', 'Fruit Juices', 4.99, 'Chilled watermelon juice with mint and lime. Incredibly refreshing on hot days.', 40),
        ('Tropical Twist', 'Fruit Juices', 5.99, 'Pineapple, mango, and passion fruit blend. An exotic escape in every sip.', 35),
        ('Beetroot Bliss', 'Vegetable Juices', 5.49, 'Beetroot, carrot, apple, and celery. Naturally sweet and full of iron.', 30),
        ('Tomato Fire', 'Vegetable Juices', 4.99, 'Spicy tomato juice with jalapeno and Worcestershire sauce. A savory treat.', 25),
        ('Peach Perfection', 'Smoothies', 6.49, 'Ripe peaches blended with vanilla yogurt and honey. Smooth and satisfying.', 20),
        ('Choco-Banana', 'Smoothies', 6.99, 'Chocolate, banana, and almond milk smoothie. Dessert that\'s actually good for you.', 25),
        ('Ginger Zinger', 'Detox Drinks', 5.99, 'Ginger, lemon, apple cider vinegar, and honey. A soothing digestive aid.', 30),
        ('Turmeric Glow', 'Detox Drinks', 7.49, 'Turmeric, ginger, coconut milk, and black pepper. Golden milk for radiant skin.', 15),
        ('Matcha Burst', 'Energy Boosters', 6.49, 'Premium matcha green tea with coconut water. Sustained energy without the jitters.', 25),
        ('Coffee Kick', 'Energy Boosters', 5.49, 'Cold brew coffee with oat milk and a touch of vanilla. Your morning ritual, perfected.', 40),
    ]

    for name, cat_name, price, desc, stock in products_data:
        product, created = Product.objects.get_or_create(
            name=name,
            defaults={
                'slug': name.lower().replace(' ', '-').replace("'", ''),
                'category': created_categories[cat_name],
                'description': desc,
                'price': price,
                'stock': stock,
                'available': True,
            }
        )
        if created:
            print(f'Created product: {name}')

    print('\nSeed completed!')
    print('Admin login: admin / admin123')
    print('Demo login: demo / demo123')


if __name__ == '__main__':
    seed()
