import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from apps.accounts.models import User, Address
from apps.catalog.models import Category, Product, ProductImage, ProductReview
from apps.orders.models import Coupon

def create_svg_image(title, subtitle, category_name, bg_color="#1e293b", accent_color="#3b82f6"):
    """
    Generates a sleek, high-resolution SVG product image.
    Guarantees no broken external image links!
    """
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{bg_color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0f172a;stop-opacity:1" />
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:{accent_color};stop-opacity:0.35" />
      <stop offset="100%" style="stop-color:{accent_color};stop-opacity:0" />
    </radialGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#000000" flood-opacity="0.4" />
    </filter>
  </defs>
  <rect width="800" height="800" fill="url(#grad)" />
  <circle cx="400" cy="380" r="260" fill="url(#glow)" />
  
  <!-- Sleek Product Podium Card -->
  <rect x="150" y="140" width="500" height="480" rx="24" fill="#ffffff" fill-opacity="0.04" stroke="#ffffff" stroke-opacity="0.12" stroke-width="2" filter="url(#shadow)" />
  
  <!-- Category Badge -->
  <rect x="300" y="170" width="200" height="34" rx="17" fill="{accent_color}" fill-opacity="0.2" stroke="{accent_color}" stroke-width="1.5" />
  <text x="400" y="193" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="13" font-weight="700" fill="#ffffff" text-anchor="middle" letter-spacing="2">{category_name.upper()}</text>

  <!-- Product Icon Shape Mockup -->
  <g transform="translate(400, 340)">
    <circle r="75" fill="{accent_color}" fill-opacity="0.15" stroke="{accent_color}" stroke-width="2" />
    <path d="M-30,-20 L30,-20 L20,30 L-20,30 Z" fill="none" stroke="#ffffff" stroke-width="3" stroke-linejoin="round" />
    <circle cx="0" cy="5" r="8" fill="{accent_color}" />
  </g>

  <!-- Product Title & Tagline -->
  <text x="400" y="480" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="24" font-weight="700" fill="#ffffff" text-anchor="middle">{title}</text>
  <text x="400" y="520" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="15" fill="#94a3b8" text-anchor="middle">{subtitle}</text>

  <!-- ShopSphere Watermark -->
  <text x="400" y="740" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="14" font-weight="600" fill="#475569" text-anchor="middle" letter-spacing="3">SHOPSPHERE PREMIUM</text>
</svg>'''
    return svg_content.encode('utf-8')


class Command(BaseCommand):
    help = 'Seeds database with realistic sample categories, products, users, addresses, and coupons'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting ShopSphere database seeding...")

        # 1. Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@shopsphere.com',
                'first_name': 'ShopSphere',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('Admin@123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / Admin@123"))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Regular Customer
        customer, created = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'alex@example.com',
                'first_name': 'Alex',
                'last_name': 'Morgan',
                'phone_number': '+1 555-019-2834',
                'is_verified': True,
            }
        )
        if created:
            customer.set_password('Customer@123')
            customer.save()
            self.stdout.write(self.style.SUCCESS("Created customer user: customer / Customer@123"))

            # Add default shipping address
            Address.objects.create(
                user=customer,
                full_name="Alex Morgan",
                phone_number="+1 555-019-2834",
                address_line1="742 Evergreen Terrace",
                address_line2="Apt 4B",
                city="Springfield",
                state="Oregon",
                postal_code="97477",
                country="United States",
                address_type="home",
                is_default=True
            )
            Address.objects.create(
                user=customer,
                full_name="Alex Morgan (Work)",
                phone_number="+1 555-019-2834",
                address_line1="100 Silicon Parkway",
                address_line2="Suite 300",
                city="Portland",
                state="Oregon",
                postal_code="97201",
                country="United States",
                address_type="work",
                is_default=False
            )

        # 3. Coupons
        coupons_data = [
            {
                'code': 'WELCOME10',
                'description': '10% off your entire first purchase',
                'discount_type': 'percentage',
                'discount_value': Decimal('10.00'),
                'min_purchase_amount': Decimal('50.00'),
                'max_discount_amount': Decimal('50.00'),
                'valid_to': timezone.now() + timezone.timedelta(days=180),
            },
            {
                'code': 'SAVE50',
                'description': 'Flat $50 off on orders of $300 or more',
                'discount_type': 'flat',
                'discount_value': Decimal('50.00'),
                'min_purchase_amount': Decimal('300.00'),
                'valid_to': timezone.now() + timezone.timedelta(days=120),
            },
            {
                'code': 'FESTIVE25',
                'description': '25% festive discount on orders above $150',
                'discount_type': 'percentage',
                'discount_value': Decimal('25.00'),
                'min_purchase_amount': Decimal('150.00'),
                'max_discount_amount': Decimal('100.00'),
                'valid_to': timezone.now() + timezone.timedelta(days=90),
            },
        ]
        for cdata in coupons_data:
            Coupon.objects.update_or_create(code=cdata['code'], defaults=cdata)

        # 4. Categories
        categories_data = [
            {
                'name': 'Electronics',
                'slug': 'electronics',
                'icon_class': 'bi-laptop',
                'description': 'Next-generation laptops, smartphones, noise-canceling headphones, and smart audio.',
                'is_featured': True,
                'accent': '#3b82f6',
            },
            {
                'name': 'Fashion',
                'slug': 'fashion',
                'icon_class': 'bi-gem',
                'description': 'Premium apparel, minimalist jackets, timeless footwear, and luxury watches.',
                'is_featured': True,
                'accent': '#ec4899',
            },
            {
                'name': 'Home and Kitchen',
                'slug': 'home-and-kitchen',
                'icon_class': 'bi-house-heart',
                'description': 'Artisan coffee makers, smart robotic vacuums, modern cookware, and ergonomic furniture.',
                'is_featured': True,
                'accent': '#10b981',
            },
            {
                'name': 'Books',
                'slug': 'books',
                'icon_class': 'bi-book',
                'description': 'Bestselling novels, system architecture guides, self-improvement, and technology classics.',
                'is_featured': True,
                'accent': '#f59e0b',
            },
            {
                'name': 'Accessories',
                'slug': 'accessories',
                'icon_class': 'bi-watch',
                'description': 'Handcrafted leather wallets, wireless charging pads, sunglasses, and travel backpacks.',
                'is_featured': True,
                'accent': '#8b5cf6',
            },
        ]

        cat_objs = {}
        for cdata in categories_data:
            cat, _ = Category.objects.update_or_create(
                slug=cdata['slug'],
                defaults={
                    'name': cdata['name'],
                    'icon_class': cdata['icon_class'],
                    'description': cdata['description'],
                    'is_featured': cdata['is_featured'],
                }
            )
            # Create SVG banner
            svg = create_svg_image(cdata['name'], cdata['description'][:40] + "...", cdata['name'], bg_color="#182234", accent_color=cdata['accent'])
            cat.image.save(f"cat_{cat.slug}.svg", ContentFile(svg), save=True)
            cat_objs[cdata['slug']] = cat

        # 5. Products
        products_data = [
            # Electronics
            {
                'category': 'electronics',
                'name': 'Aura Sound Pro Wireless Noise-Cancelling Headphones',
                'sku': 'EL-HP-001',
                'short_description': 'Industry-leading Active Noise Cancellation with 40-hour battery life and spatial audio.',
                'description': 'Experience studio-grade acoustics anywhere. Aura Sound Pro features 45mm custom drivers, hybrid active noise cancellation, memory-foam ear cushions, and seamless multi-device Bluetooth 5.3 pairing. Includes premium carrying case and fast USB-C charge.',
                'specifications': 'Driver Size: 45mm Neodymium | Battery Life: 40 Hours | Connectivity: Bluetooth 5.3 & 3.5mm Aux | Noise Cancellation: Hybrid Active ANC | Weight: 250g | Warranty: 2 Years',
                'price': Decimal('249.99'),
                'original_price': Decimal('329.99'),
                'stock': 35,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#3b82f6',
            },
            {
                'category': 'electronics',
                'name': 'UltraBook Pro 15-inch M3 Laptop',
                'sku': 'EL-LP-002',
                'short_description': 'Stunning 4K Retina display, 16-Core Neural Engine, and all-day 18hr battery.',
                'description': 'Engineered for developers, designers, and creators. Powered by an advanced 12-core processor with 32GB unified RAM and 1TB ultra-fast PCIe NVMe SSD. Ultra-light aluminum unibody chassis with MagSafe charging.',
                'specifications': 'Processor: 12-Core High Performance CPU | RAM: 32GB Unified Memory | Storage: 1TB NVMe SSD | Display: 15.6" 4K OLED HDR (120Hz) | Battery: 18 Hours | Ports: 3x Thunderbolt 4, HDMI, SDXC',
                'price': Decimal('1499.00'),
                'original_price': Decimal('1799.00'),
                'stock': 18,
                'is_featured': True,
                'is_bestseller': False,
                'is_new_arrival': True,
                'accent': '#0284c7',
            },
            {
                'category': 'electronics',
                'name': 'PulseFit Smart Watch Series X',
                'sku': 'EL-SW-003',
                'short_description': 'Advanced ECG, SpO2 sensor, Always-on AMOLED display, and 50m water resistance.',
                'description': 'Stay connected and monitor your health around the clock. Features real-time heart rate tracking, sleep cycle analysis, GPS workout routing, and emergency crash detection in a lightweight aerospace titanium casing.',
                'specifications': 'Display: 1.9" AMOLED Always-on (1000 nits) | Water Resistance: 50 Meters (5 ATM) | Sensors: ECG, SpO2, Optical Heart, Gyro | Battery: 48 Hours Typical | Case Material: Titanium Grade 5',
                'price': Decimal('299.00'),
                'original_price': Decimal('349.00'),
                'stock': 42,
                'is_featured': False,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#2563eb',
            },
            {
                'category': 'electronics',
                'name': 'TrueBass 360 Portable Waterproof Speaker',
                'sku': 'EL-SP-004',
                'short_description': 'Room-filling 360-degree sound with deep bass and IPX7 rugged waterproof design.',
                'description': 'Take vibrant sound to the pool, beach, or campground. Features dual passive radiators, 24-hour continuous playback, built-in speakerphone mic, and party sync pairing for up to 100 speakers.',
                'specifications': 'Output: 30W RMS | Battery: 24 Hours (7500 mAh) | Rating: IPX7 Waterproof & Dustproof | Range: 30m Bluetooth | Weight: 680g',
                'price': Decimal('89.99'),
                'original_price': Decimal('119.99'),
                'stock': 50,
                'is_featured': False,
                'is_bestseller': False,
                'is_new_arrival': True,
                'accent': '#1d4ed8',
            },

            # Fashion
            {
                'category': 'fashion',
                'name': 'Heritage Italian Leather Chelsea Boots',
                'sku': 'FA-BT-005',
                'short_description': 'Full-grain Tuscan calfskin leather with Goodyear welt construction.',
                'description': 'Handcrafted in Italy using vegetable-tanned calfskin. Features elasticated side gussets, stacked leather heel with Vibram rubber half-sole for superior grip, and cushioned leather insole that molds to your feet.',
                'specifications': 'Material: 100% Full-grain Tuscan Calfskin | Construction: Goodyear Welted | Sole: Vibram Lugged Rubber Half-sole | Lining: Soft Glove Leather | Origin: Florence, Italy',
                'price': Decimal('210.00'),
                'original_price': Decimal('260.00'),
                'stock': 22,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#ec4899',
            },
            {
                'category': 'fashion',
                'name': 'Minimalist Merino Wool Crewneck Sweater',
                'sku': 'FA-SW-006',
                'short_description': 'Extra-fine 100% Australian Merino wool with natural temperature regulation.',
                'description': 'An everyday luxury staple. Incredibly soft against the skin, breathable, and naturally odor-resistant. Ribbed collar, cuffs, and hem ensure shape retention wash after wash.',
                'specifications': 'Fabric: 100% Extra-fine Merino Wool (19.5 Micron) | Fit: Tailored Modern Regular | Care: Machine wash cold wool cycle or dry clean | Colors: Charcoal Grey, Navy, Camel',
                'price': Decimal('95.00'),
                'original_price': Decimal('125.00'),
                'stock': 30,
                'is_featured': False,
                'is_bestseller': True,
                'is_new_arrival': True,
                'accent': '#f43f5e',
            },
            {
                'category': 'fashion',
                'name': 'Urban Commuter Weatherproof Field Jacket',
                'sku': 'FA-JK-007',
                'short_description': 'Water-resistant coated cotton canvas with reinforced elbows and 6 utility pockets.',
                'description': 'Built for variable city climates. Features storm flap zipper closure, hidden packable hood, brass hardware, and interior fleece lining for crisp mornings.',
                'specifications': 'Outer: 100% Wax-coated Heavy Cotton Canvas | Lining: Thermal Poly-fleece | Pockets: 4 Exterior Cargo + 2 Internal Security | Hardware: Antique Brass YKK Zippers',
                'price': Decimal('165.00'),
                'original_price': Decimal('210.00'),
                'stock': 15,
                'is_featured': True,
                'is_bestseller': False,
                'is_new_arrival': False,
                'accent': '#e11d48',
            },
            {
                'category': 'fashion',
                'name': 'Tailored Slim-Fit Chino Trousers',
                'sku': 'FA-CH-008',
                'short_description': 'Stretch organic cotton twill designed for effortless transition from desk to dinner.',
                'description': 'Versatile trousers crafted with 98% organic cotton and 2% elastane for unrestricted movement. Includes deep coin pocket and wrinkle-resistant finish.',
                'specifications': 'Material: 98% Organic Cotton, 2% Elastane | Cut: Slim Tapered | Rise: Mid Rise | Closure: Horn Button & Metal Zip',
                'price': Decimal('68.00'),
                'original_price': Decimal('85.00'),
                'stock': 40,
                'is_featured': False,
                'is_bestseller': False,
                'is_new_arrival': True,
                'accent': '#db2777',
            },

            # Home and Kitchen
            {
                'category': 'home-and-kitchen',
                'name': 'Barista Touch Espresso & Cappuccino Machine',
                'sku': 'HK-EM-009',
                'short_description': '15-Bar Italian pump with integrated conical burr grinder and digital PID temperature.',
                'description': 'Become your own master barista. Features thermo-block rapid heating system ready in 3 seconds, intuitive touchscreen controls, micro-foam steam wand for latte art, and single/double shot customization.',
                'specifications': 'Pressure: 15-Bar Italian High-Pressure Pump | Water Tank: 2.0 Liters | Grinder: 30 Grind Settings Conical Burr | Heating: 3-Second ThermoJet | Power: 1680W',
                'price': Decimal('549.99'),
                'original_price': Decimal('699.99'),
                'stock': 12,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#10b981',
            },
            {
                'category': 'home-and-kitchen',
                'name': 'RoboClean LiDAR Robot Vacuum & Mop',
                'sku': 'HK-RV-010',
                'short_description': '5000Pa extreme suction with 3D obstacle avoidance and multi-floor precision mapping.',
                'description': 'Autonomous floor care that leaves surfaces sparkling clean. Dual spinning mop pads scrub sticky spills, while LiDAR laser sensor navigates complex chair legs and carpets with automated mop lifting.',
                'specifications': 'Suction Power: 5000 Pa | Navigation: LiDAR + 3D Structured Light | Runtime: 180 Minutes (5200 mAh) | Dustbin: 450ml | Water Tank: 200ml Electronically Controlled',
                'price': Decimal('389.00'),
                'original_price': Decimal('499.00'),
                'stock': 20,
                'is_featured': True,
                'is_bestseller': False,
                'is_new_arrival': True,
                'accent': '#059669',
            },
            {
                'category': 'home-and-kitchen',
                'name': 'Artisan Enameled Cast Iron Dutch Oven (6 Quart)',
                'sku': 'HK-DO-011',
                'short_description': 'Heavy cast iron for unbeatable heat retention, slow-cooking stews and crusty breads.',
                'description': 'A kitchen heirloom. Chip-resistant enamel interior requires no pre-seasoning. Oven-safe up to 500°F with stainless steel knob and ergonomic loop handles for secure transport.',
                'specifications': 'Capacity: 6.0 Quarts | Material: Heavy Cast Iron with 3-Layer Porcelain Enamel | Oven Safe: Up to 500°F (260°C) | Compatibility: Induction, Gas, Electric, Ceramic',
                'price': Decimal('119.50'),
                'original_price': Decimal('149.50'),
                'stock': 25,
                'is_featured': False,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#047857',
            },
            {
                'category': 'home-and-kitchen',
                'name': 'Ergonomic Natural Bamboo Standing Desk Converter',
                'sku': 'HK-SD-012',
                'short_description': 'Smooth pneumatic gas spring height adjustment for dual monitor workstations.',
                'description': 'Elevate your workday posture in seconds. 100% sustainable moso bamboo desktop with spacious lower tier for ergonomic keyboard and mouse placement.',
                'specifications': 'Surface Dimensions: 36" x 22" | Height Range: 4.7" to 19.7" | Weight Capacity: 35 lbs | Mechanism: Gas Spring Assist',
                'price': Decimal('159.00'),
                'original_price': Decimal('199.00'),
                'stock': 16,
                'is_featured': False,
                'is_bestseller': False,
                'is_new_arrival': True,
                'accent': '#065f46',
            },

            # Books
            {
                'category': 'books',
                'name': 'Designing Data-Intensive Applications',
                'sku': 'BK-DDIA-013',
                'short_description': 'The definitive guide to distributed databases, reliability, scalability, and maintainability.',
                'description': 'By Martin Kleppmann. Explore the fundamental principles behind building scalable systems. Covers storage engines, replication algorithms, partitioning, transactions, consensus, and batch/stream processing.',
                'specifications': 'Author: Martin Kleppmann | Publisher: O\'Reilly Media | Pages: 616 | Format: Paperback / Hardcover | Language: English | ISBN: 978-1449373320',
                'price': Decimal('42.50'),
                'original_price': Decimal('54.99'),
                'stock': 45,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#f59e0b',
            },
            {
                'category': 'books',
                'name': 'Clean Code: A Handbook of Agile Software Craftsmanship',
                'sku': 'BK-CC-014',
                'short_description': 'The legendary classic on writing readable, testable, and maintainable software.',
                'description': 'By Robert C. Martin (Uncle Bob). Discover the principles, patterns, and practices of writing clean code. Learn how to craft good names, format functions, handle errors gracefully, and refactor messy codebases.',
                'specifications': 'Author: Robert C. Martin | Publisher: Prentice Hall | Pages: 464 | Format: Paperback | Language: English | ISBN: 978-0132350884',
                'price': Decimal('38.00'),
                'original_price': Decimal('49.99'),
                'stock': 35,
                'is_featured': False,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#d97706',
            },
            {
                'category': 'books',
                'name': 'Atomic Habits: An Easy & Proven Way to Build Good Habits',
                'sku': 'BK-AH-015',
                'short_description': 'Over 15 million copies sold. Transform your life with tiny changes that deliver remarkable results.',
                'description': 'By James Clear. Learn practical strategies that will teach you exactly how to form good habits, break bad ones, and master the tiny behaviors that lead to remarkable results.',
                'specifications': 'Author: James Clear | Publisher: Avery | Pages: 320 | Format: Hardcover | Language: English | ISBN: 978-0735211292',
                'price': Decimal('24.00'),
                'original_price': Decimal('30.00'),
                'stock': 60,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#b45309',
            },
            {
                'category': 'books',
                'name': 'System Design Interview: An Insider\'s Guide (Volume 2)',
                'sku': 'BK-SDI-016',
                'short_description': 'Master large-scale system design for senior software engineer and architect interviews.',
                'description': 'By Alex Xu and Sahn Lam. Step-by-step real-world blueprints: payment systems, digital wallet, stock exchange, live streaming, cloud storage (S3), and distributed message queues.',
                'specifications': 'Author: Alex Xu, Sahn Lam | Pages: 490 | Format: Paperback | Illustrated: Yes (Full diagrams) | ISBN: 979-8664653403',
                'price': Decimal('39.95'),
                'original_price': Decimal('49.95'),
                'stock': 28,
                'is_featured': False,
                'is_bestseller': False,
                'is_new_arrival': True,
                'accent': '#92400e',
            },

            # Accessories
            {
                'category': 'accessories',
                'name': 'Nomad Pro Leather Bifold Wallet with RFID Shield',
                'sku': 'AC-WL-017',
                'short_description': 'Ultra-slim Horween full-grain leather wallet with integrated anti-theft RFID blocking.',
                'description': 'Holds up to 10 cards and flat cash without pocket bulge. Features dedicated pull-tab quick access slot for daily credit cards and hidden coin/key compartment.',
                'specifications': 'Leather: American Horween Vegetable-Tanned | Capacity: 8-12 Cards + Cash | Protection: 13.56 MHz RFID Blocking Layer | Dimensions: 4.1" x 3.1" x 0.4"',
                'price': Decimal('55.00'),
                'original_price': Decimal('70.00'),
                'stock': 40,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#8b5cf6',
            },
            {
                'category': 'accessories',
                'name': 'TitanShield 3-in-1 Fast Wireless Charging Station',
                'sku': 'AC-WC-018',
                'short_description': 'Foldable MagSafe charging dock for Phone, Watch, and wireless earbuds simultaneously.',
                'description': 'Declutter your nightstand or desk. Fast 15W Qi-certified magnetic wireless charging with weighted aluminum alloy base and intelligent heat dissipation.',
                'specifications': 'Output: 15W Phone + 5W Watch + 5W Earbuds | Cable: 4ft USB-C to USB-C Included | Compatibility: MagSafe iPhones, Apple Watch, AirPods/Galaxy Buds',
                'price': Decimal('69.99'),
                'original_price': Decimal('89.99'),
                'stock': 30,
                'is_featured': False,
                'is_bestseller': False,
                'is_new_arrival': True,
                'accent': '#7c3aed',
            },
            {
                'category': 'accessories',
                'name': 'AeroFlight Water-Resistant Everyday Travel Backpack (28L)',
                'sku': 'AC-BP-019',
                'short_description': 'TSA-friendly checkpoint layout with 16" padded laptop sleeve and luggage pass-through.',
                'description': 'Designed for seamless airport travel and daily commutes. Crafted from ballistic 840D Cordura nylon with hidden passport pocket and expandable water bottle holder.',
                'specifications': 'Capacity: 28 Liters | Fabric: 840D Ballistic Cordura Nylon | Laptop Sleeve: Up to 16.2" Laptop | Zippers: YKK AquaGuard Weatherproof | Weight: 1.1 kg',
                'price': Decimal('135.00'),
                'original_price': Decimal('175.00'),
                'stock': 24,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'accent': '#6d28d9',
            },
            {
                'category': 'accessories',
                'name': 'Apex Polarized Aviation Sunglasses with UV400',
                'sku': 'AC-SG-020',
                'short_description': 'Featherweight Japanese titanium frames with anti-reflective polarized optical lenses.',
                'description': 'Timeless classic aviator silhouette reinvented with modern materials. Total UV400 protection eliminates blinding glare without color distortion.',
                'specifications': 'Frame: Beta-Titanium (18 grams) | Lens: High-clarity Triacetate Cellulose (TAC) Polarized | UV Protection: 100% UVA/UVB (UV400) | Case: Hard Leatherette Case Included',
                'price': Decimal('85.00'),
                'original_price': Decimal('110.00'),
                'stock': 0,  # Demonstrating Out of Stock badge!
                'is_featured': False,
                'is_bestseller': False,
                'is_new_arrival': True,
                'accent': '#5b21b6',
            },
        ]

        for pdata in products_data:
            cat = cat_objs[pdata['category']]
            prod, _ = Product.objects.update_or_create(
                sku=pdata['sku'],
                defaults={
                    'category': cat,
                    'name': pdata['name'],
                    'short_description': pdata['short_description'],
                    'description': pdata['description'],
                    'specifications': pdata['specifications'],
                    'price': pdata['price'],
                    'original_price': pdata['original_price'],
                    'stock': pdata['stock'],
                    'is_active': True,
                    'is_featured': pdata['is_featured'],
                    'is_bestseller': pdata['is_bestseller'],
                    'is_new_arrival': pdata['is_new_arrival'],
                }
            )

            # Generate and attach SVG cover image
            svg_cover = create_svg_image(
                title=prod.name[:28],
                subtitle=f"${prod.price:.2f} · {cat.name}",
                category_name=cat.name,
                bg_color="#0f172a",
                accent_color=pdata['accent']
            )
            prod.cover_image.save(f"prod_{prod.slug}.svg", ContentFile(svg_cover), save=True)

            # Generate gallery images
            if prod.gallery_images.count() == 0:
                for idx in range(1, 3):
                    svg_gallery = create_svg_image(
                        title=f"{prod.name[:25]} - Angle {idx}",
                        subtitle="Detailed Specification Showcase",
                        category_name=cat.name,
                        bg_color="#1e293b",
                        accent_color=pdata['accent']
                    )
                    gal_img = ProductImage(product=prod, display_order=idx, alt_text=f"{prod.name} angle {idx}")
                    gal_img.image.save(f"gal_{prod.slug}_{idx}.svg", ContentFile(svg_gallery), save=True)

            # Add sample review
            if prod.reviews.count() == 0 and customer:
                review_ratings = [5, 4, 5, 5, 4]
                r_rating = review_ratings[len(prod.name) % len(review_ratings)]
                ProductReview.objects.create(
                    product=prod,
                    user=customer,
                    rating=r_rating,
                    title=f"Impressive quality and exceeded my expectations!",
                    comment=f"I purchased this {prod.category.name.lower()} item two weeks ago. The build quality, packaging, and attention to detail are superb. Would definitely recommend to anyone looking for genuine quality.",
                    is_approved=True
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(categories_data)} categories and {len(products_data)} products!"))
