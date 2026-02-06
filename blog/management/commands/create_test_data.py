from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region


class Command(BaseCommand):
    help = 'Create test data for blog functionality'

    def handle(self, *args, **options):
        # Create superuser if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@test.com', 'admin123')

        # Create categories and subcategories
        tech_cat, created = Category.objects.get_or_create(
            name='Technology',
            defaults={'description': 'All things tech related'}
        )

        business_cat, created = Category.objects.get_or_create(
            name='Business',
            defaults={'description': 'Business and entrepreneurship'}
        )

        # Create subcategories
        SubCategory.objects.get_or_create(
            category=tech_cat,
            name='Web Development',
            defaults={'description': 'Web development tutorials and tips'}
        )

        SubCategory.objects.get_or_create(
            category=tech_cat,
            name='Mobile Apps',
            defaults={'description': 'Mobile application development'}
        )

        SubCategory.objects.get_or_create(
            category=business_cat,
            name='Startups',
            defaults={'description': 'Startup advice and stories'}
        )

        SubCategory.objects.get_or_create(
            category=business_cat,
            name='Marketing',
            defaults={'description': 'Digital marketing strategies'}
        )

        # Create location data
        india, created = Country.objects.get_or_create(
            name='India',
            code='IND',
            defaults={}
        )

        maharashtra, created = State.objects.get_or_create(
            name='Maharashtra',
            code='MH',
            country=india,
            defaults={}
        )

        mumbai, created = City.objects.get_or_create(
            name='Mumbai',
            state=maharashtra,
            defaults={'is_capital': False, 'population': 20411000}
        )

        mumbai_district, created = District.objects.get_or_create(
            name='Mumbai City',
            city=mumbai,
            defaults={}
        )

        Region.objects.get_or_create(
            name='Andheri',
            district=mumbai_district,
            defaults={'description': 'Western suburb of Mumbai'}
        )

        Region.objects.get_or_create(
            name='Bandra',
            district=mumbai_district,
            defaults={'description': 'Affluent suburb of Mumbai'}
        )

        # Create another city/state for variety
        karnataka, created = State.objects.get_or_create(
            name='Karnataka',
            code='KA',
            country=india,
            defaults={}
        )

        bangalore, created = City.objects.get_or_create(
            name='Bangalore',
            state=karnataka,
            defaults={'is_capital': True, 'population': 8443675}
        )

        bangalore_district, created = District.objects.get_or_create(
            name='Bangalore Urban',
            city=bangalore,
            defaults={}
        )

        Region.objects.get_or_create(
            name='Koramangala',
            district=bangalore_district,
            defaults={'description': 'Tech hub of Bangalore'}
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully created test data for categories, subcategories, and locations')
        )
