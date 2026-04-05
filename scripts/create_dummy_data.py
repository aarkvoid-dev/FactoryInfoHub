#!/usr/bin/env python
"""
Script to create dummy data for FactoryInfoHub project.
Creates a superuser and optional sample data.

Usage:
    python3 manage.py shell < scripts/create_dummy_data.py
    
Or run directly:
    python3 scripts/create_dummy_data.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')
django.setup()

from django.contrib.auth.models import User
from Accounts.models import Profile
from location.models import Country, State, City, District
from category.models import Category, SubCategory
from blog.models import Post
from Karkahan.models import Factory
from Workers.models import Worker
from faq.models import FAQQuestion


def create_superuser():
    """Create a superuser account."""
    print("Creating superuser...")
    
    # Check if superuser already exists
    if User.objects.filter(username='admin').exists():
        print("Superuser 'admin' already exists.")
        return User.objects.get(username='admin')
    
    # Create superuser
    user = User.objects.create_superuser(
        username='admin',
        email='admin@factoryinfohub.com',
        password='Admin@123456',
        first_name='Super',
        last_name='Admin'
    )
    
    # Create profile for superuser
    Profile.objects.get_or_create(
        user=user,
        defaults={
            'phone': '+91 9876543210',
            'is_verified': True,
        }
    )
    
    print(f"Superuser created: username='admin', password='Admin@123456'")
    return user


def create_location_data():
    """Create comprehensive location data for all Indian states and major cities."""
    print("\nCreating location data for India...")
    
    # Create India
    india, created = Country.objects.get_or_create(
        name='India',
        code='IN',
    )
    
    # Indian States and Union Territories with their major cities
    indian_states = {
        'Andhra Pradesh': {
            'code': 'AP',
            'cities': [
                {'name': 'Visakhapatnam', 'is_capital': True, 'districts': ['Visakhapatnam', 'Anakapalli']},
                {'name': 'Vijayawada', 'is_capital': False, 'districts': ['NTR', 'Krishna']},
                {'name': 'Guntur', 'is_capital': False, 'districts': ['Guntur', 'Palnadu']},
                {'name': 'Tirupati', 'is_capital': False, 'districts': ['Tirupati', 'Chittoor']},
                {'name': 'Nellore', 'is_capital': False, 'districts': ['Nellore', 'Sri Potti Sriramulu']},
            ]
        },
        'Arunachal Pradesh': {
            'code': 'AR',
            'cities': [
                {'name': 'Itanagar', 'is_capital': True, 'districts': ['Papum Pare', 'Lower Subansiri']},
                {'name': 'Naharlagun', 'is_capital': False, 'districts': ['Papum Pare']},
                {'name': 'Pasighat', 'is_capital': False, 'districts': ['East Siang']},
            ]
        },
        'Assam': {
            'code': 'AS',
            'cities': [
                {'name': 'Dispur', 'is_capital': True, 'districts': ['Kamrup Metropolitan']},
                {'name': 'Guwahati', 'is_capital': False, 'districts': ['Kamrup Metropolitan', 'Kamrup']},
                {'name': 'Silchar', 'is_capital': False, 'districts': ['Cachar', 'Hailakandi']},
                {'name': 'Dibrugarh', 'is_capital': False, 'districts': ['Dibrugarh', 'Tinsukia']},
                {'name': 'Jorhat', 'is_capital': False, 'districts': ['Jorhat', 'Majuli']},
            ]
        },
        'Bihar': {
            'code': 'BR',
            'cities': [
                {'name': 'Patna', 'is_capital': True, 'districts': ['Patna', 'Nalanda']},
                {'name': 'Gaya', 'is_capital': False, 'districts': ['Gaya', 'Nawada']},
                {'name': 'Bhagalpur', 'is_capital': False, 'districts': ['Bhagalpur', 'Banka']},
                {'name': 'Muzaffarpur', 'is_capital': False, 'districts': ['Muzaffarpur', 'Vaishali']},
                {'name': 'Darbhanga', 'is_capital': False, 'districts': ['Darbhanga', 'Madhubani']},
            ]
        },
        'Chhattisgarh': {
            'code': 'CG',
            'cities': [
                {'name': 'Raipur', 'is_capital': True, 'districts': ['Raipur', 'Durg']},
                {'name': 'Bhilai', 'is_capital': False, 'districts': ['Durg']},
                {'name': 'Bilaspur', 'is_capital': False, 'districts': ['Bilaspur', 'Korba']},
                {'name': 'Korba', 'is_capital': False, 'districts': ['Korba']},
                {'name': 'Durg', 'is_capital': False, 'districts': ['Durg', 'Bemetara']},
            ]
        },
        'Goa': {
            'code': 'GA',
            'cities': [
                {'name': 'Panaji', 'is_capital': True, 'districts': ['North Goa']},
                {'name': 'Margao', 'is_capital': False, 'districts': ['South Goa']},
                {'name': 'Vasco da Gama', 'is_capital': False, 'districts': ['South Goa']},
                {'name': 'Mapusa', 'is_capital': False, 'districts': ['North Goa']},
            ]
        },
        'Gujarat': {
            'code': 'GJ',
            'cities': [
                {'name': 'Gandhinagar', 'is_capital': True, 'districts': ['Gandhinagar']},
                {'name': 'Ahmedabad', 'is_capital': False, 'districts': ['Ahmedabad', 'Ahmedabad Rural']},
                {'name': 'Surat', 'is_capital': False, 'districts': ['Surat', 'Tapi']},
                {'name': 'Vadodara', 'is_capital': False, 'districts': ['Vadodara']},
                {'name': 'Rajkot', 'is_capital': False, 'districts': ['Rajkot']},
                {'name': 'Bhavnagar', 'is_capital': False, 'districts': ['Bhavnagar']},
                {'name': 'Jamnagar', 'is_capital': False, 'districts': ['Jamnagar', 'Devbhoomi Dwarka']},
            ]
        },
        'Haryana': {
            'code': 'HR',
            'cities': [
                {'name': 'Chandigarh', 'is_capital': True, 'districts': ['Chandigarh']},
                {'name': 'Faridabad', 'is_capital': False, 'districts': ['Faridabad', 'Nuh']},
                {'name': 'Gurugram', 'is_capital': False, 'districts': ['Gurugram', 'Rewari']},
                {'name': 'Panipat', 'is_capital': False, 'districts': ['Panipat']},
                {'name': 'Ambala', 'is_capital': False, 'districts': ['Ambala']},
                {'name': 'Karnal', 'is_capital': False, 'districts': ['Karnal']},
            ]
        },
        'Himachal Pradesh': {
            'code': 'HP',
            'cities': [
                {'name': 'Shimla', 'is_capital': True, 'districts': ['Shimla']},
                {'name': 'Dharamshala', 'is_capital': False, 'districts': ['Kangra']},
                {'name': 'Manali', 'is_capital': False, 'districts': ['Kullu']},
                {'name': 'Kullu', 'is_capital': False, 'districts': ['Kullu', 'Lahaul and Spiti']},
                {'name': 'Mandi', 'is_capital': False, 'districts': ['Mandi']},
            ]
        },
        'Jharkhand': {
            'code': 'JH',
            'cities': [
                {'name': 'Ranchi', 'is_capital': True, 'districts': ['Ranchi', 'Khunti']},
                {'name': 'Jamshedpur', 'is_capital': False, 'districts': ['East Singhbhum']},
                {'name': 'Dhanbad', 'is_capital': False, 'districts': ['Dhanbad', 'Bokaro']},
                {'name': 'Bokaro', 'is_capital': False, 'districts': ['Bokaro']},
                {'name': 'Deoghar', 'is_capital': False, 'districts': ['Deoghar', 'Dumka']},
            ]
        },
        'Karnataka': {
            'code': 'KA',
            'cities': [
                {'name': 'Bengaluru', 'is_capital': True, 'districts': ['Bengaluru Urban', 'Bengaluru Rural']},
                {'name': 'Mysuru', 'is_capital': False, 'districts': ['Mysuru', 'Chamarajanagar']},
                {'name': 'Mangaluru', 'is_capital': False, 'districts': ['Dakshina Kannada']},
                {'name': 'Hubballi', 'is_capital': False, 'districts': ['Dharwad']},
                {'name': 'Belagavi', 'is_capital': False, 'districts': ['Belagavi']},
                {'name': 'Kalaburagi', 'is_capital': False, 'districts': ['Kalaburagi', 'Yadgir']},
            ]
        },
        'Kerala': {
            'code': 'KL',
            'cities': [
                {'name': 'Thiruvananthapuram', 'is_capital': True, 'districts': ['Thiruvananthapuram']},
                {'name': 'Kochi', 'is_capital': False, 'districts': ['Ernakulam']},
                {'name': 'Kozhikode', 'is_capital': False, 'districts': ['Kozhikode', 'Malappuram']},
                {'name': 'Thrissur', 'is_capital': False, 'districts': ['Thrissur']},
                {'name': 'Kollam', 'is_capital': False, 'districts': ['Kollam']},
                {'name': 'Alappuzha', 'is_capital': False, 'districts': ['Alappuzha']},
            ]
        },
        'Madhya Pradesh': {
            'code': 'MP',
            'cities': [
                {'name': 'Bhopal', 'is_capital': True, 'districts': ['Bhopal', 'Raisen']},
                {'name': 'Indore', 'is_capital': False, 'districts': ['Indore', 'Dhar']},
                {'name': 'Gwalior', 'is_capital': False, 'districts': ['Gwalior', 'Bhind']},
                {'name': 'Jabalpur', 'is_capital': False, 'districts': ['Jabalpur', 'Narsinghpur']},
                {'name': 'Ujjain', 'is_capital': False, 'districts': ['Ujjain']},
                {'name': 'Sagar', 'is_capital': False, 'districts': ['Sagar', 'Damoh']},
            ]
        },
        'Maharashtra': {
            'code': 'MH',
            'cities': [
                {'name': 'Mumbai', 'is_capital': True, 'districts': ['Mumbai City', 'Mumbai Suburban']},
                {'name': 'Pune', 'is_capital': False, 'districts': ['Pune']},
                {'name': 'Nagpur', 'is_capital': False, 'districts': ['Nagpur', 'Wardha']},
                {'name': 'Nashik', 'is_capital': False, 'districts': ['Nashik', 'Dhule']},
                {'name': 'Aurangabad', 'is_capital': False, 'districts': ['Aurangabad', 'Jalna']},
                {'name': 'Solapur', 'is_capital': False, 'districts': ['Solapur']},
                {'name': 'Kolhapur', 'is_capital': False, 'districts': ['Kolhapur', 'Sangli']},
                {'name': 'Amravati', 'is_capital': False, 'districts': ['Amravati', 'Akola']},
            ]
        },
        'Manipur': {
            'code': 'MN',
            'cities': [
                {'name': 'Imphal', 'is_capital': True, 'districts': ['Imphal West', 'Imphal East']},
                {'name': 'Thoubal', 'is_capital': False, 'districts': ['Thoubal']},
                {'name': 'Bishnupur', 'is_capital': False, 'districts': ['Bishnupur']},
            ]
        },
        'Meghalaya': {
            'code': 'ML',
            'cities': [
                {'name': 'Shillong', 'is_capital': True, 'districts': ['East Khasi Hills']},
                {'name': 'Tura', 'is_capital': False, 'districts': ['West Garo Hills']},
                {'name': 'Jowai', 'is_capital': False, 'districts': ['West Jaintia Hills']},
            ]
        },
        'Mizoram': {
            'code': 'MZ',
            'cities': [
                {'name': 'Aizawl', 'is_capital': True, 'districts': ['Aizawl']},
                {'name': 'Lunglei', 'is_capital': False, 'districts': ['Lunglei']},
                {'name': 'Champhai', 'is_capital': False, 'districts': ['Champhai']},
            ]
        },
        'Nagaland': {
            'code': 'NL',
            'cities': [
                {'name': 'Kohima', 'is_capital': True, 'districts': ['Kohima']},
                {'name': 'Dimapur', 'is_capital': False, 'districts': ['Dimapur']},
                {'name': 'Mokokchung', 'is_capital': False, 'districts': ['Mokokchung']},
            ]
        },
        'Odisha': {
            'code': 'OR',
            'cities': [
                {'name': 'Bhubaneswar', 'is_capital': True, 'districts': ['Khordha', 'Puri']},
                {'name': 'Cuttack', 'is_capital': False, 'districts': ['Cuttack', 'Jagatsinghpur']},
                {'name': 'Rourkela', 'is_capital': False, 'districts': ['Sundargarh']},
                {'name': 'Berhampur', 'is_capital': False, 'districts': ['Ganjam']},
                {'name': 'Sambalpur', 'is_capital': False, 'districts': ['Sambalpur', 'Jharsuguda']},
            ]
        },
        'Punjab': {
            'code': 'PB',
            'cities': [
                {'name': 'Chandigarh', 'is_capital': True, 'districts': ['Chandigarh']},
                {'name': 'Ludhiana', 'is_capital': False, 'districts': ['Ludhiana']},
                {'name': 'Amritsar', 'is_capital': False, 'districts': ['Amritsar', 'Tarn Taran']},
                {'name': 'Jalandhar', 'is_capital': False, 'districts': ['Jalandhar', 'Kapurthala']},
                {'name': 'Patiala', 'is_capital': False, 'districts': ['Patiala', 'Fatehgarh Sahib']},
                {'name': 'Bathinda', 'is_capital': False, 'districts': ['Bathinda', 'Mansa']},
            ]
        },
        'Rajasthan': {
            'code': 'RJ',
            'cities': [
                {'name': 'Jaipur', 'is_capital': True, 'districts': ['Jaipur', 'Dausa']},
                {'name': 'Jodhpur', 'is_capital': False, 'districts': ['Jodhpur', 'Nagaur']},
                {'name': 'Udaipur', 'is_capital': False, 'districts': ['Udaipur', 'Rajsamand']},
                {'name': 'Kota', 'is_capital': False, 'districts': ['Kota', 'Bundi']},
                {'name': 'Ajmer', 'is_capital': False, 'districts': ['Ajmer', 'Tonk']},
                {'name': 'Bikaner', 'is_capital': False, 'districts': ['Bikaner']},
                {'name': 'Alwar', 'is_capital': False, 'districts': ['Alwar']},
            ]
        },
        'Sikkim': {
            'code': 'SK',
            'cities': [
                {'name': 'Gangtok', 'is_capital': True, 'districts': ['East Sikkim']},
                {'name': 'Namchi', 'is_capital': False, 'districts': ['South Sikkim']},
                {'name': 'Gyalshing', 'is_capital': False, 'districts': ['West Sikkim']},
            ]
        },
        'Tamil Nadu': {
            'code': 'TN',
            'cities': [
                {'name': 'Chennai', 'is_capital': True, 'districts': ['Chennai', 'Kanchipuram']},
                {'name': 'Coimbatore', 'is_capital': False, 'districts': ['Coimbatore', 'Tiruppur']},
                {'name': 'Madurai', 'is_capital': False, 'districts': ['Madurai', 'Theni']},
                {'name': 'Tiruchirappalli', 'is_capital': False, 'districts': ['Tiruchirappalli', 'Karur']},
                {'name': 'Salem', 'is_capital': False, 'districts': ['Salem', 'Namakkal']},
                {'name': 'Tirunelveli', 'is_capital': False, 'districts': ['Tirunelveli', 'Tenkasi']},
                {'name': 'Vellore', 'is_capital': False, 'districts': ['Vellore', 'Ranipet']},
            ]
        },
        'Telangana': {
            'code': 'TG',
            'cities': [
                {'name': 'Hyderabad', 'is_capital': True, 'districts': ['Hyderabad', 'Rangareddy']},
                {'name': 'Warangal', 'is_capital': False, 'districts': ['Warangal Urban', 'Warangal Rural']},
                {'name': 'Nizamabad', 'is_capital': False, 'districts': ['Nizamabad']},
                {'name': 'Karimnagar', 'is_capital': False, 'districts': ['Karimnagar']},
                {'name': 'Khammam', 'is_capital': False, 'districts': ['Khammam', 'Bhadradri']},
            ]
        },
        'Tripura': {
            'code': 'TR',
            'cities': [
                {'name': 'Agartala', 'is_capital': True, 'districts': ['West Tripura']},
                {'name': 'Udaipur', 'is_capital': False, 'districts': ['Gomati']},
                {'name': 'Dharmanagar', 'is_capital': False, 'districts': ['North Tripura']},
            ]
        },
        'Uttar Pradesh': {
            'code': 'UP',
            'cities': [
                {'name': 'Lucknow', 'is_capital': True, 'districts': ['Lucknow', 'Unnao']},
                {'name': 'Kanpur', 'is_capital': False, 'districts': ['Kanpur Nagar', 'Kanpur Dehat']},
                {'name': 'Varanasi', 'is_capital': False, 'districts': ['Varanasi', 'Chandauli']},
                {'name': 'Prayagraj', 'is_capital': False, 'districts': ['Prayagraj', 'Kaushambi']},
                {'name': 'Agra', 'is_capital': False, 'districts': ['Agra', 'Firozabad']},
                {'name': 'Meerut', 'is_capital': False, 'districts': ['Meerut', 'Baghpat']},
                {'name': 'Bareilly', 'is_capital': False, 'districts': ['Bareilly', 'Pilibhit']},
                {'name': 'Aligarh', 'is_capital': False, 'districts': ['Aligarh', 'Hathras']},
                {'name': 'Moradabad', 'is_capital': False, 'districts': ['Moradabad', 'Rampur']},
                {'name': 'Saharanpur', 'is_capital': False, 'districts': ['Saharanpur', 'Shamli']},
            ]
        },
        'Uttarakhand': {
            'code': 'UK',
            'cities': [
                {'name': 'Dehradun', 'is_capital': True, 'districts': ['Dehradun']},
                {'name': 'Haridwar', 'is_capital': False, 'districts': ['Haridwar']},
                {'name': 'Rishikesh', 'is_capital': False, 'districts': ['Dehradun']},
                {'name': 'Nainital', 'is_capital': False, 'districts': ['Nainital', 'Almora']},
                {'name': 'Mussoorie', 'is_capital': False, 'districts': ['Dehradun']},
            ]
        },
        'West Bengal': {
            'code': 'WB',
            'cities': [
                {'name': 'Kolkata', 'is_capital': True, 'districts': ['Kolkata', 'North 24 Parganas']},
                {'name': 'Howrah', 'is_capital': False, 'districts': ['Howrah']},
                {'name': 'Durgapur', 'is_capital': False, 'districts': ['Paschim Bardhaman']},
                {'name': 'Asansol', 'is_capital': False, 'districts': ['Paschim Bardhaman']},
                {'name': 'Siliguri', 'is_capital': False, 'districts': ['Darjeeling', 'Jalpaiguri']},
                {'name': 'Malda', 'is_capital': False, 'districts': ['Malda', 'Dakshin Dinajpur']},
            ]
        },
        # Union Territories
        'Andaman and Nicobar Islands': {
            'code': 'AN',
            'cities': [
                {'name': 'Port Blair', 'is_capital': True, 'districts': ['South Andaman']},
                {'name': 'Diglipur', 'is_capital': False, 'districts': ['North and Middle Andaman']},
            ]
        },
        'Chandigarh': {
            'code': 'CH',
            'cities': [
                {'name': 'Chandigarh', 'is_capital': True, 'districts': ['Chandigarh']},
            ]
        },
        'Dadra and Nagar Haveli and Daman and Diu': {
            'code': 'DN',
            'cities': [
                {'name': 'Daman', 'is_capital': True, 'districts': ['Daman']},
                {'name': 'Silvassa', 'is_capital': False, 'districts': ['Dadra and Nagar Haveli']},
                {'name': 'Diu', 'is_capital': False, 'districts': ['Diu']},
            ]
        },
        'Delhi': {
            'code': 'DL',
            'cities': [
                {'name': 'New Delhi', 'is_capital': True, 'districts': ['New Delhi', 'South Delhi']},
                {'name': 'Central Delhi', 'is_capital': False, 'districts': ['Central Delhi', 'North Delhi']},
                {'name': 'East Delhi', 'is_capital': False, 'districts': ['East Delhi', 'Shahdara']},
                {'name': 'West Delhi', 'is_capital': False, 'districts': ['West Delhi']},
                {'name': 'Dwarka', 'is_capital': False, 'districts': ['South West Delhi']},
                {'name': 'Rohini', 'is_capital': False, 'districts': ['North West Delhi']},
            ]
        },
        'Jammu and Kashmir': {
            'code': 'JK',
            'cities': [
                {'name': 'Srinagar', 'is_capital': True, 'districts': ['Srinagar', 'Ganderbal']},
                {'name': 'Jammu', 'is_capital': False, 'districts': ['Jammu', 'Samba']},
                {'name': 'Anantnag', 'is_capital': False, 'districts': ['Anantnag', 'Kulgam']},
                {'name': 'Baramulla', 'is_capital': False, 'districts': ['Baramulla', 'Kupwara']},
                {'name': 'Udhampur', 'is_capital': False, 'districts': ['Udhampur', 'Reasi']},
            ]
        },
        'Ladakh': {
            'code': 'LA',
            'cities': [
                {'name': 'Leh', 'is_capital': True, 'districts': ['Leh']},
                {'name': 'Kargil', 'is_capital': False, 'districts': ['Kargil']},
            ]
        },
        'Lakshadweep': {
            'code': 'LD',
            'cities': [
                {'name': 'Kavaratti', 'is_capital': True, 'districts': ['Lakshadweep']},
                {'name': 'Agatti', 'is_capital': False, 'districts': ['Lakshadweep']},
            ]
        },
        'Puducherry': {
            'code': 'PY',
            'cities': [
                {'name': 'Puducherry', 'is_capital': True, 'districts': ['Puducherry']},
                {'name': 'Karaikal', 'is_capital': False, 'districts': ['Karaikal']},
                {'name': 'Yanam', 'is_capital': False, 'districts': ['Yanam']},
                {'name': 'Mahe', 'is_capital': False, 'districts': ['Mahe']},
            ]
        },
    }
    
    total_states = 0
    total_cities = 0
    total_districts = 0
    
    for state_name, state_data in indian_states.items():
        state, state_created = State.objects.get_or_create(
            country=india,
            name=state_name,
            defaults={
                'code': state_data['code'],
            }
        )
        if state_created:
            total_states += 1
        
        for city_data in state_data['cities']:
            city, city_created = City.objects.get_or_create(
                state=state,
                name=city_data['name'],
                defaults={
                    'is_capital': city_data['is_capital'],
                }
            )
            if city_created:
                total_cities += 1
            
            for district_name in city_data['districts']:
                district, district_created = District.objects.get_or_create(
                    city=city,
                    name=district_name,
                )
                if district_created:
                    total_districts += 1
    
    print(f"Location data created:")
    print(f"  - States/UTs: {total_states}")
    print(f"  - Cities: {total_cities}")
    print(f"  - Districts: {total_districts}")


def create_category_data():
    """Create sample category and subcategory data."""
    print("\nCreating category data...")
    
    categories_data = [
        {
            'name': 'Textile',
            'description': 'Textile and fabric manufacturing',
            'subcategories': ['Cotton Textiles', 'Synthetic Textiles', 'Handloom', 'Garments']
        },
        {
            'name': 'Automotive',
            'description': 'Automotive parts and manufacturing',
            'subcategories': ['Auto Parts', 'Two Wheelers', 'Commercial Vehicles', 'Electric Vehicles']
        },
        {
            'name': 'Electronics',
            'description': 'Electronics and technology',
            'subcategories': ['Consumer Electronics', 'Semiconductors', 'IoT Devices', 'Home Appliances']
        },
        {
            'name': 'Pharmaceuticals',
            'description': 'Pharmaceutical and healthcare',
            'subcategories': ['Generic Drugs', 'Vaccines', 'Medical Devices', 'Ayurvedic']
        },
        {
            'name': 'Food Processing',
            'description': 'Food and beverage processing',
            'subcategories': ['Packaged Foods', 'Beverages', 'Dairy Products', 'Snacks']
        },
        {
            'name': 'Chemicals',
            'description': 'Chemical manufacturing',
            'subcategories': ['Industrial Chemicals', 'Agrochemicals', 'Specialty Chemicals', 'Petrochemicals']
        },
        {
            'name': 'Metal Works',
            'description': 'Metal fabrication and works',
            'subcategories': ['Steel Fabrication', 'Aluminum Products', 'Copper Products', 'Casting']
        },
        {
            'name': 'Plastics',
            'description': 'Plastic manufacturing and products',
            'subcategories': ['Plastic Packaging', 'Plastic Pipes', 'Plastic Molding', 'Recycled Plastics']
        },
    ]
    
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'description': cat_data['description'],
            }
        )
        
        # Create subcategories
        for subcat_name in cat_data['subcategories']:
            SubCategory.objects.get_or_create(
                category=category,
                name=subcat_name,
                defaults={
                    'description': f'{subcat_name} under {cat_data["name"]}',
                }
            )
    
    print(f"Created {len(categories_data)} categories with subcategories")


def create_factory_data(user):
    """Create sample factory data."""
    print("\nCreating factory data...")
    
    try:
        category = Category.objects.first()
        if not category:
            print("No categories found. Run create_category_data() first.")
            return
        
        subcategory = SubCategory.objects.first()
        if not subcategory:
            print("No subcategories found. Run create_category_data() first.")
            return
        
        # Get location data
        india = Country.objects.first()
        if not india:
            print("No country found. Run create_location_data() first.")
            return
        
        state = State.objects.first()
        if not state:
            print("No state found. Run create_location_data() first.")
            return
        
        city = City.objects.first()
        if not city:
            print("No city found. Run create_location_data() first.")
            return
        
        district = District.objects.first()
        
        factories = [
            {
                'name': 'ABC Textiles Pvt Ltd',
                'description': 'Leading textile manufacturer specializing in cotton fabrics and garments.',
                'category': category,
                'subcategory': subcategory,
                'country': india,
                'state': state,
                'city': city,
                'district': district,
                'address': 'Plot No. 123, MIDC Industrial Area',
                'pincode': '400001',
                'contact_person': 'Rajesh Sharma',
                'contact_phone': '+91 9876543211',
                'contact_email': 'info@abctextiles.com',
                'website': 'https://abctextiles.com',
                'established_year': 2005,
                'employee_count': 250,
                'created_by': user,
                'factory_type': 'Manufacturing',
                'production_capacity': '10000 units/month',
                'working_hours': '9:00 AM - 6:00 PM',
            },
            {
                'name': 'XYZ Automotive Components',
                'description': 'Precision automotive parts manufacturer for leading car companies.',
                'category': category,
                'subcategory': subcategory,
                'country': india,
                'state': state,
                'city': city,
                'district': district,
                'address': 'Survey No. 456, Industrial Estate',
                'pincode': '411001',
                'contact_person': 'Amit Patel',
                'contact_phone': '+91 9876543212',
                'contact_email': 'contact@xyzauto.com',
                'website': 'https://xyzauto.com',
                'established_year': 2010,
                'employee_count': 180,
                'created_by': user,
                'factory_type': 'Assembly',
                'production_capacity': '5000 units/month',
                'working_hours': '8:00 AM - 5:00 PM',
            },
        ]
        
        for factory_data in factories:
            Factory.objects.get_or_create(
                name=factory_data['name'],
                defaults=factory_data
            )
        
        print(f"Created {len(factories)} factories")
    except Exception as e:
        print(f"Error creating factory data: {e}")


def create_worker_data():
    """Create sample worker data."""
    print("\nCreating worker data...")
    
    try:
        category = Category.objects.first()
        if not category:
            print("No categories found. Run create_category_data() first.")
            return
        
        factory = Factory.objects.first()
        if not factory:
            print("No factories found. Run create_factory_data() first.")
            return
        
        workers = [
            {
                'full_name': 'Rajesh Kumar',
                'date_of_birth': '1985-05-15',
                'gender': 'M',
                'phone_number': '+91 9876543213',
                'email': 'rajesh@example.com',
                'category': category,
                'years_of_experience': 8,
                'skills': 'Machine Operation, Quality Control, Textile Manufacturing',
                'availability': 'FT',
                'expected_daily_wage': 800.00,
                'country': factory.country,
                'state': factory.state,
                'city': factory.city,
                'district': factory.district,
                'address': 'Room No. 12, Worker Colony',
                'created_by': factory.created_by,
            },
            {
                'full_name': 'Sunita Devi',
                'date_of_birth': '1990-08-20',
                'gender': 'F',
                'phone_number': '+91 9876543214',
                'email': 'sunita@example.com',
                'category': category,
                'years_of_experience': 5,
                'skills': 'Assembly, Packaging, Quality Inspection',
                'availability': 'FT',
                'expected_daily_wage': 600.00,
                'country': factory.country,
                'state': factory.state,
                'city': factory.city,
                'district': factory.district,
                'address': 'Room No. 15, Worker Colony',
                'created_by': factory.created_by,
            },
        ]
        
        for worker_data in workers:
            Worker.objects.get_or_create(
                full_name=worker_data['full_name'],
                defaults=worker_data
            )
        
        print(f"Created {len(workers)} workers")
    except Exception as e:
        print(f"Error creating worker data: {e}")


def create_blog_data(user):
    """Create sample blog posts."""
    print("\nCreating blog data...")
    
    try:
        posts = [
            {
                'title': 'Welcome to FactoryInfoHub',
                'slug': 'welcome-to-factoryinfohub',
                'content': '''
                    <h2>About FactoryInfoHub</h2>
                    <p>FactoryInfoHub is your one-stop platform for discovering and connecting with manufacturing units across India. We aim to bridge the gap between manufacturers and buyers, creating a transparent and efficient ecosystem.</p>
                    
                    <h3>Our Mission</h3>
                    <p>To empower small and medium-scale manufacturers by providing them with a digital platform to showcase their capabilities and connect with potential buyers worldwide.</p>
                    
                    <h3>Key Features</h3>
                    <ul>
                        <li>Comprehensive factory database</li>
                        <li>Detailed worker information</li>
                        <li>Category-wise classification</li>
                        <li>Location-based search</li>
                        <li>Real-time updates</li>
                    </ul>
                ''',
                'excerpt': 'Welcome to FactoryInfoHub - your gateway to India\'s manufacturing ecosystem.',
                'author': user,
                'status': 'published',
            },
            {
                'title': 'How to Use FactoryInfoHub Effectively',
                'slug': 'how-to-use-factoryinfohub-effectively',
                'content': '''
                    <h2>Getting Started with FactoryInfoHub</h2>
                    <p>FactoryInfoHub offers a comprehensive platform for exploring India\'s manufacturing landscape. Here\'s how to make the most of it:</p>
                    
                    <h3>For Buyers</h3>
                    <ol>
                        <li><strong>Search by Category:</strong> Use our category filter to find manufacturers in your specific industry.</li>
                        <li><strong>Location-based Search:</strong> Find factories near your location to reduce logistics costs.</li>
                        <li><strong>Verify Credentials:</strong> Check factory details, employee count, and establishment year.</li>
                        <li><strong>Contact Directly:</strong> Use the provided contact information to reach out to manufacturers.</li>
                    </ol>
                    
                    <h3>For Manufacturers</h3>
                    <ol>
                        <li><strong>Create Detailed Profile:</strong> Provide comprehensive information about your capabilities.</li>
                        <li><strong>Update Regularly:</strong> Keep your factory information current.</li>
                        <li><strong>Add Photos:</strong> Showcase your infrastructure and products.</li>
                        <li><strong>Respond Promptly:</strong> Reply to inquiries in a timely manner.</li>
                    </ol>
                ''',
                'excerpt': 'Learn how to effectively use FactoryInfoHub to connect with manufacturers and buyers.',
                'author': user,
                'status': 'published',
            },
        ]
        
        for post_data in posts:
            Post.objects.get_or_create(
                slug=post_data['slug'],
                defaults=post_data
            )
        
        print(f"Created {len(posts)} blog posts")
    except Exception as e:
        print(f"Error creating blog data: {e}")


def create_faq_data():
    """Create sample FAQ data using FAQQuestion model."""
    print("\nCreating FAQ data...")
    
    try:
        # Get or create a category for FAQs
        general_category, created = Category.objects.get_or_create(
            name='General',
            defaults={'description': 'General questions about FactoryInfoHub'}
        )
        manufacturers_category, created = Category.objects.get_or_create(
            name='For Manufacturers',
            defaults={'description': 'Questions for factory owners and manufacturers'}
        )
        buyers_category, created = Category.objects.get_or_create(
            name='For Buyers',
            defaults={'description': 'Questions for buyers and purchasers'}
        )
        
        # Create FAQ questions
        faqs = [
            {
                'title': 'What is FactoryInfoHub?',
                'category': general_category,
                'question_text': 'What is FactoryInfoHub and what does it do?',
                'answer_text': 'FactoryInfoHub is a comprehensive platform that provides information about manufacturing units across India, including their capabilities, workforce, and contact details. It helps buyers find manufacturers and manufacturers showcase their capabilities.',
                'status': 'published',
                'is_featured': True,
                'order': 1,
            },
            {
                'title': 'How can I register my factory?',
                'category': manufacturers_category,
                'question_text': 'How can I register my factory on FactoryInfoHub?',
                'answer_text': 'You can register your factory by creating an account on FactoryInfoHub and submitting your factory details through the registration form. Our team will verify the information before publishing your listing.',
                'status': 'published',
                'is_featured': True,
                'order': 2,
            },
            {
                'title': 'Is it free to use FactoryInfoHub?',
                'category': buyers_category,
                'question_text': 'Is it free to use FactoryInfoHub?',
                'answer_text': 'Yes, basic usage of FactoryInfoHub is completely free. Buyers can search and contact manufacturers at no cost. We offer premium features for manufacturers who want enhanced visibility and additional tools.',
                'status': 'published',
                'is_featured': True,
                'order': 3,
            },
        ]
        
        for faq_data in faqs:
            FAQQuestion.objects.get_or_create(
                title=faq_data['title'],
                defaults=faq_data
            )
        
        print(f"Created {len(faqs)} FAQ questions in {3} categories")
    except Exception as e:
        print(f"Error creating FAQ data: {e}")


def main():
    """Main function to create all dummy data."""
    print("=" * 60)
    print("FactoryInfoHub Dummy Data Generator")
    print("=" * 60)
    
    # Create superuser first
    admin_user = create_superuser()
    
    # Create location data
    create_location_data()
    
    # Create category data
    create_category_data()
    
    # Create factory data
    create_factory_data(admin_user)
    
    # Create worker data
    create_worker_data()
    
    # Create blog data
    create_blog_data(admin_user)
    
    # Create FAQ data
    create_faq_data()
    
    print("\n" + "=" * 60)
    print("Dummy data creation completed!")
    print("=" * 60)
    print("\nSuperuser credentials:")
    print("  Username: admin")
    print("  Password: Admin@123456")
    print("\nYou can now log in to the admin panel at /admin/")


if __name__ == '__main__':
    main()