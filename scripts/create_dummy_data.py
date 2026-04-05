#!/usr/bin/env python
"""
Script to create dummy data for FactoryInfoHub project.
Creates a superuser and optional sample data.

Usage:
    python manage.py shell < scripts/create_dummy_data.py
    
Or run directly:
    python scripts/create_dummy_data.py
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
from category.models import Category
from blog.models import Post
from Karkahan.models import Factory
from Workers.models import Worker
from faq.models import FAQ, FAQCategory


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
        defaults={'name_hi': 'भारत'}
    )
    
    # Indian States and Union Territories with their major cities
    # Format: {state_name: {state_code, name_hi, cities: [city_name, name_hi, is_capital, districts: [district_names]]}}
    indian_states = {
        'Andhra Pradesh': {
            'code': 'AP',
            'name_hi': 'आंध्र प्रदेश',
            'cities': [
                {'name': 'Visakhapatnam', 'name_hi': 'विशाखपत्तनम', 'is_capital': True, 'districts': ['Visakhapatnam', 'Anakapalli']},
                {'name': 'Vijayawada', 'name_hi': 'विजयवाड़ा', 'is_capital': False, 'districts': ['NTR', 'Krishna']},
                {'name': 'Guntur', 'name_hi': 'गुंटूर', 'is_capital': False, 'districts': ['Guntur', 'Palnadu']},
                {'name': 'Tirupati', 'name_hi': 'तिरुपति', 'is_capital': False, 'districts': ['Tirupati', 'Chittoor']},
                {'name': 'Nellore', 'name_hi': 'नेल्लोर', 'is_capital': False, 'districts': ['Nellore', 'Sri Potti Sriramulu']},
            ]
        },
        'Arunachal Pradesh': {
            'code': 'AR',
            'name_hi': 'अरुणाचल प्रदेश',
            'cities': [
                {'name': 'Itanagar', 'name_hi': 'इटानगर', 'is_capital': True, 'districts': ['Papum Pare', 'Lower Subansiri']},
                {'name': 'Naharlagun', 'name_hi': 'नहरलागुन', 'is_capital': False, 'districts': ['Papum Pare']},
                {'name': 'Pasighat', 'name_hi': 'पासीघाट', 'is_capital': False, 'districts': ['East Siang']},
            ]
        },
        'Assam': {
            'code': 'AS',
            'name_hi': 'असम',
            'cities': [
                {'name': 'Dispur', 'name_hi': 'दिसपुर', 'is_capital': True, 'districts': ['Kamrup Metropolitan']},
                {'name': 'Guwahati', 'name_hi': 'गुवाहाटी', 'is_capital': False, 'districts': ['Kamrup Metropolitan', 'Kamrup']},
                {'name': 'Silchar', 'name_hi': 'सिलचर', 'is_capital': False, 'districts': ['Cachar', 'Hailakandi']},
                {'name': 'Dibrugarh', 'name_hi': 'डिब्रूगढ़', 'is_capital': False, 'districts': ['Dibrugarh', 'Tinsukia']},
                {'name': 'Jorhat', 'name_hi': 'जोरहाट', 'is_capital': False, 'districts': ['Jorhat', 'Majuli']},
            ]
        },
        'Bihar': {
            'code': 'BR',
            'name_hi': 'बिहार',
            'cities': [
                {'name': 'Patna', 'name_hi': 'पटना', 'is_capital': True, 'districts': ['Patna', 'Nalanda']},
                {'name': 'Gaya', 'name_hi': 'गया', 'is_capital': False, 'districts': ['Gaya', 'Nawada']},
                {'name': 'Bhagalpur', 'name_hi': 'भागलपुर', 'is_capital': False, 'districts': ['Bhagalpur', 'Banka']},
                {'name': 'Muzaffarpur', 'name_hi': 'मुजफ्फरपुर', 'is_capital': False, 'districts': ['Muzaffarpur', 'Vaishali']},
                {'name': 'Darbhanga', 'name_hi': 'दरभंगा', 'is_capital': False, 'districts': ['Darbhanga', 'Madhubani']},
            ]
        },
        'Chhattisgarh': {
            'code': 'CG',
            'name_hi': 'छत्तीसगढ़',
            'cities': [
                {'name': 'Raipur', 'name_hi': 'रायपुर', 'is_capital': True, 'districts': ['Raipur', 'Durg']},
                {'name': 'Bhilai', 'name_hi': 'भिलाई', 'is_capital': False, 'districts': ['Durg']},
                {'name': 'Bilaspur', 'name_hi': 'बिलासपुर', 'is_capital': False, 'districts': ['Bilaspur', 'Korba']},
                {'name': 'Korba', 'name_hi': 'कोरबा', 'is_capital': False, 'districts': ['Korba']},
                {'name': 'Durg', 'name_hi': 'दुर्ग', 'is_capital': False, 'districts': ['Durg', 'Bemetara']},
            ]
        },
        'Goa': {
            'code': 'GA',
            'name_hi': 'गोवा',
            'cities': [
                {'name': 'Panaji', 'name_hi': 'पणजी', 'is_capital': True, 'districts': ['North Goa']},
                {'name': 'Margao', 'name_hi': 'मडगांव', 'is_capital': False, 'districts': ['South Goa']},
                {'name': 'Vasco da Gama', 'name_hi': 'वासको द गामा', 'is_capital': False, 'districts': ['South Goa']},
                {'name': 'Mapusa', 'name_hi': 'मपुसा', 'is_capital': False, 'districts': ['North Goa']},
            ]
        },
        'Gujarat': {
            'code': 'GJ',
            'name_hi': 'गुजरात',
            'cities': [
                {'name': 'Gandhinagar', 'name_hi': 'गांधीनगर', 'is_capital': True, 'districts': ['Gandhinagar']},
                {'name': 'Ahmedabad', 'name_hi': 'अहमदाबाद', 'is_capital': False, 'districts': ['Ahmedabad', 'Ahmedabad Rural']},
                {'name': 'Surat', 'name_hi': 'सूरत', 'is_capital': False, 'districts': ['Surat', 'Tapi']},
                {'name': 'Vadodara', 'name_hi': 'वडोदरा', 'is_capital': False, 'districts': ['Vadodara']},
                {'name': 'Rajkot', 'name_hi': 'राजकोट', 'is_capital': False, 'districts': ['Rajkot']},
                {'name': 'Bhavnagar', 'name_hi': 'भावनगर', 'is_capital': False, 'districts': ['Bhavnagar']},
                {'name': 'Jamnagar', 'name_hi': 'जामनगर', 'is_capital': False, 'districts': ['Jamnagar', 'Devbhoomi Dwarka']},
            ]
        },
        'Haryana': {
            'code': 'HR',
            'name_hi': 'हरियाणा',
            'cities': [
                {'name': 'Chandigarh', 'name_hi': 'चंडीगढ़', 'is_capital': True, 'districts': ['Chandigarh']},
                {'name': 'Faridabad', 'name_hi': 'फरीदाबाद', 'is_capital': False, 'districts': ['Faridabad', 'Nuh']},
                {'name': 'Gurugram', 'name_hi': 'गुरुग्राम', 'is_capital': False, 'districts': ['Gurugram', 'Rewari']},
                {'name': 'Panipat', 'name_hi': 'पानीपत', 'is_capital': False, 'districts': ['Panipat']},
                {'name': 'Ambala', 'name_hi': 'अंबाला', 'is_capital': False, 'districts': ['Ambala']},
                {'name': 'Karnal', 'name_hi': 'करनाल', 'is_capital': False, 'districts': ['Karnal']},
            ]
        },
        'Himachal Pradesh': {
            'code': 'HP',
            'name_hi': 'हिमाचल प्रदेश',
            'cities': [
                {'name': 'Shimla', 'name_hi': 'शिमला', 'is_capital': True, 'districts': ['Shimla']},
                {'name': 'Dharamshala', 'name_hi': 'धर्मशाला', 'is_capital': False, 'districts': ['Kangra']},
                {'name': 'Manali', 'name_hi': 'मनाली', 'is_capital': False, 'districts': ['Kullu']},
                {'name': 'Kullu', 'name_hi': 'कुल्लू', 'is_capital': False, 'districts': ['Kullu', 'Lahaul and Spiti']},
                {'name': 'Mandi', 'name_hi': 'मंडी', 'is_capital': False, 'districts': ['Mandi']},
            ]
        },
        'Jharkhand': {
            'code': 'JH',
            'name_hi': 'झारखंड',
            'cities': [
                {'name': 'Ranchi', 'name_hi': 'रांची', 'is_capital': True, 'districts': ['Ranchi', 'Khunti']},
                {'name': 'Jamshedpur', 'name_hi': 'जमशेदपुर', 'is_capital': False, 'districts': ['East Singhbhum']},
                {'name': 'Dhanbad', 'name_hi': 'धनबाद', 'is_capital': False, 'districts': ['Dhanbad', 'Bokaro']},
                {'name': 'Bokaro', 'name_hi': 'बोकारो', 'is_capital': False, 'districts': ['Bokaro']},
                {'name': 'Deoghar', 'name_hi': 'देवघर', 'is_capital': False, 'districts': ['Deoghar', 'Dumka']},
            ]
        },
        'Karnataka': {
            'code': 'KA',
            'name_hi': 'कर्नाटक',
            'cities': [
                {'name': 'Bengaluru', 'name_hi': 'बेंगलुरु', 'is_capital': True, 'districts': ['Bengaluru Urban', 'Bengaluru Rural']},
                {'name': 'Mysuru', 'name_hi': 'मैसूर', 'is_capital': False, 'districts': ['Mysuru', 'Chamarajanagar']},
                {'name': 'Mangaluru', 'name_hi': 'मंगलुरु', 'is_capital': False, 'districts': ['Dakshina Kannada']},
                {'name': 'Hubballi', 'name_hi': 'हुब्बल्ली', 'is_capital': False, 'districts': ['Dharwad']},
                {'name': 'Belagavi', 'name_hi': 'बेलागवी', 'is_capital': False, 'districts': ['Belagavi']},
                {'name': 'Kalaburagi', 'name_hi': 'कलबुर्गी', 'is_capital': False, 'districts': ['Kalaburagi', 'Yadgir']},
            ]
        },
        'Kerala': {
            'code': 'KL',
            'name_hi': 'केरल',
            'cities': [
                {'name': 'Thiruvananthapuram', 'name_hi': 'तिरुवनंतपुरम', 'is_capital': True, 'districts': ['Thiruvananthapuram']},
                {'name': 'Kochi', 'name_hi': 'कोच्चि', 'is_capital': False, 'districts': ['Ernakulam']},
                {'name': 'Kozhikode', 'name_hi': 'कोझिकोड', 'is_capital': False, 'districts': ['Kozhikode', 'Malappuram']},
                {'name': 'Thrissur', 'name_hi': 'त्रिस्सूर', 'is_capital': False, 'districts': ['Thrissur']},
                {'name': 'Kollam', 'name_hi': 'कोल्लम', 'is_capital': False, 'districts': ['Kollam']},
                {'name': 'Alappuzha', 'name_hi': 'आलप्पुझा', 'is_capital': False, 'districts': ['Alappuzha']},
            ]
        },
        'Madhya Pradesh': {
            'code': 'MP',
            'name_hi': 'मध्य प्रदेश',
            'cities': [
                {'name': 'Bhopal', 'name_hi': 'भोपाल', 'is_capital': True, 'districts': ['Bhopal', 'Raisen']},
                {'name': 'Indore', 'name_hi': 'इंदौर', 'is_capital': False, 'districts': ['Indore', 'Dhar']},
                {'name': 'Gwalior', 'name_hi': 'ग्वालियर', 'is_capital': False, 'districts': ['Gwalior', 'Bhind']},
                {'name': 'Jabalpur', 'name_hi': 'जबलपुर', 'is_capital': False, 'districts': ['Jabalpur', 'Narsinghpur']},
                {'name': 'Ujjain', 'name_hi': 'उज्जैन', 'is_capital': False, 'districts': ['Ujjain']},
                {'name': 'Sagar', 'name_hi': 'सागर', 'is_capital': False, 'districts': ['Sagar', 'Damoh']},
            ]
        },
        'Maharashtra': {
            'code': 'MH',
            'name_hi': 'महाराष्ट्र',
            'cities': [
                {'name': 'Mumbai', 'name_hi': 'मुंबई', 'is_capital': True, 'districts': ['Mumbai City', 'Mumbai Suburban']},
                {'name': 'Pune', 'name_hi': 'पुणे', 'is_capital': False, 'districts': ['Pune']},
                {'name': 'Nagpur', 'name_hi': 'नागपुर', 'is_capital': False, 'districts': ['Nagpur', 'Wardha']},
                {'name': 'Nashik', 'name_hi': 'नाशिक', 'is_capital': False, 'districts': ['Nashik', 'Dhule']},
                {'name': 'Aurangabad', 'name_hi': 'औरंगाबाद', 'is_capital': False, 'districts': ['Aurangabad', 'Jalna']},
                {'name': 'Solapur', 'name_hi': 'सोलापुर', 'is_capital': False, 'districts': ['Solapur']},
                {'name': 'Kolhapur', 'name_hi': 'कोल्हापुर', 'is_capital': False, 'districts': ['Kolhapur', 'Sangli']},
                {'name': 'Amravati', 'name_hi': 'अमरावती', 'is_capital': False, 'districts': ['Amravati', 'Akola']},
            ]
        },
        'Manipur': {
            'code': 'MN',
            'name_hi': 'मणिपुर',
            'cities': [
                {'name': 'Imphal', 'name_hi': 'इंफाल', 'is_capital': True, 'districts': ['Imphal West', 'Imphal East']},
                {'name': 'Thoubal', 'name_hi': 'थौबल', 'is_capital': False, 'districts': ['Thoubal']},
                {'name': 'Bishnupur', 'name_hi': 'विष्णुपुर', 'is_capital': False, 'districts': ['Bishnupur']},
            ]
        },
        'Meghalaya': {
            'code': 'ML',
            'name_hi': 'मेघालय',
            'cities': [
                {'name': 'Shillong', 'name_hi': 'शिलांग', 'is_capital': True, 'districts': ['East Khasi Hills']},
                {'name': 'Tura', 'name_hi': 'तुरा', 'is_capital': False, 'districts': ['West Garo Hills']},
                {'name': 'Jowai', 'name_hi': 'जोवाई', 'is_capital': False, 'districts': ['West Jaintia Hills']},
            ]
        },
        'Mizoram': {
            'code': 'MZ',
            'name_hi': 'मिजोरम',
            'cities': [
                {'name': 'Aizawl', 'name_hi': 'आइजोल', 'is_capital': True, 'districts': ['Aizawl']},
                {'name': 'Lunglei', 'name_hi': 'लुंगलई', 'is_capital': False, 'districts': ['Lunglei']},
                {'name': 'Champhai', 'name_hi': 'चम्फई', 'is_capital': False, 'districts': ['Champhai']},
            ]
        },
        'Nagaland': {
            'code': 'NL',
            'name_hi': 'नागालैंड',
            'cities': [
                {'name': 'Kohima', 'name_hi': 'कोहिमा', 'is_capital': True, 'districts': ['Kohima']},
                {'name': 'Dimapur', 'name_hi': 'दिमापुर', 'is_capital': False, 'districts': ['Dimapur']},
                {'name': 'Mokokchung', 'name_hi': 'मोकोकचुंग', 'is_capital': False, 'districts': ['Mokokchung']},
            ]
        },
        'Odisha': {
            'code': 'OR',
            'name_hi': 'ओडिशा',
            'cities': [
                {'name': 'Bhubaneswar', 'name_hi': 'भुवनेश्वर', 'is_capital': True, 'districts': ['Khordha', 'Puri']},
                {'name': 'Cuttack', 'name_hi': 'कटक', 'is_capital': False, 'districts': ['Cuttack', 'Jagatsinghpur']},
                {'name': 'Rourkela', 'name_hi': 'रूरकेला', 'is_capital': False, 'districts': ['Sundargarh']},
                {'name': 'Berhampur', 'name_hi': 'बरहामपुर', 'is_capital': False, 'districts': ['Ganjam']},
                {'name': 'Sambalpur', 'name_hi': 'संभलपुर', 'is_capital': False, 'districts': ['Sambalpur', 'Jharsuguda']},
            ]
        },
        'Punjab': {
            'code': 'PB',
            'name_hi': 'पंजाब',
            'cities': [
                {'name': 'Chandigarh', 'name_hi': 'चंडीगढ़', 'is_capital': True, 'districts': ['Chandigarh']},
                {'name': 'Ludhiana', 'name_hi': 'लुधियाना', 'is_capital': False, 'districts': ['Ludhiana']},
                {'name': 'Amritsar', 'name_hi': 'अमृतसर', 'is_capital': False, 'districts': ['Amritsar', 'Tarn Taran']},
                {'name': 'Jalandhar', 'name_hi': 'जालंधर', 'is_capital': False, 'districts': ['Jalandhar', 'Kapurthala']},
                {'name': 'Patiala', 'name_hi': 'पटियाला', 'is_capital': False, 'districts': ['Patiala', 'Fatehgarh Sahib']},
                {'name': 'Bathinda', 'name_hi': 'भटिंडा', 'is_capital': False, 'districts': ['Bathinda', 'Mansa']},
            ]
        },
        'Rajasthan': {
            'code': 'RJ',
            'name_hi': 'राजस्थान',
            'cities': [
                {'name': 'Jaipur', 'name_hi': 'जयपुर', 'is_capital': True, 'districts': ['Jaipur', 'Dausa']},
                {'name': 'Jodhpur', 'name_hi': 'जोधपुर', 'is_capital': False, 'districts': ['Jodhpur', 'Nagaur']},
                {'name': 'Udaipur', 'name_hi': 'उदयपुर', 'is_capital': False, 'districts': ['Udaipur', 'Rajsamand']},
                {'name': 'Kota', 'name_hi': 'कोटा', 'is_capital': False, 'districts': ['Kota', 'Bundi']},
                {'name': 'Ajmer', 'name_hi': 'अजमेर', 'is_capital': False, 'districts': ['Ajmer', 'Tonk']},
                {'name': 'Bikaner', 'name_hi': 'बीकानेर', 'is_capital': False, 'districts': ['Bikaner']},
                {'name': 'Alwar', 'name_hi': 'अलवर', 'is_capital': False, 'districts': ['Alwar']},
            ]
        },
        'Sikkim': {
            'code': 'SK',
            'name_hi': 'सिक्किम',
            'cities': [
                {'name': 'Gangtok', 'name_hi': 'गंगटोक', 'is_capital': True, 'districts': ['East Sikkim']},
                {'name': 'Namchi', 'name_hi': 'नामची', 'is_capital': False, 'districts': ['South Sikkim']},
                {'name': 'Gyalshing', 'name_hi': 'ग्यालशिंग', 'is_capital': False, 'districts': ['West Sikkim']},
            ]
        },
        'Tamil Nadu': {
            'code': 'TN',
            'name_hi': 'तमिलनाडु',
            'cities': [
                {'name': 'Chennai', 'name_hi': 'चेन्नई', 'is_capital': True, 'districts': ['Chennai', 'Kanchipuram']},
                {'name': 'Coimbatore', 'name_hi': 'कोयंबटूर', 'is_capital': False, 'districts': ['Coimbatore', 'Tiruppur']},
                {'name': 'Madurai', 'name_hi': 'मदुरै', 'is_capital': False, 'districts': ['Madurai', 'Theni']},
                {'name': 'Tiruchirappalli', 'name_hi': 'तिरुचिरापल्ली', 'is_capital': False, 'districts': ['Tiruchirappalli', 'Karur']},
                {'name': 'Salem', 'name_hi': 'सेलम', 'is_capital': False, 'districts': ['Salem', 'Namakkal']},
                {'name': 'Tirunelveli', 'name_hi': 'तिरुनेलवेली', 'is_capital': False, 'districts': ['Tirunelveli', 'Tenkasi']},
                {'name': 'Vellore', 'name_hi': 'वेल्लोर', 'is_capital': False, 'districts': ['Vellore', 'Ranipet']},
            ]
        },
        'Telangana': {
            'code': 'TG',
            'name_hi': 'तेलंगाना',
            'cities': [
                {'name': 'Hyderabad', 'name_hi': 'हैदराबाद', 'is_capital': True, 'districts': ['Hyderabad', 'Rangareddy']},
                {'name': 'Warangal', 'name_hi': 'वारंगल', 'is_capital': False, 'districts': ['Warangal Urban', 'Warangal Rural']},
                {'name': 'Nizamabad', 'name_hi': 'निजामाबाद', 'is_capital': False, 'districts': ['Nizamabad']},
                {'name': 'Karimnagar', 'name_hi': 'करिमनगर', 'is_capital': False, 'districts': ['Karimnagar']},
                {'name': 'Khammam', 'name_hi': 'खम्मम', 'is_capital': False, 'districts': ['Khammam', 'Bhadradri']},
            ]
        },
        'Tripura': {
            'code': 'TR',
            'name_hi': 'त्रिपुरा',
            'cities': [
                {'name': 'Agartala', 'name_hi': 'अगरतला', 'is_capital': True, 'districts': ['West Tripura']},
                {'name': 'Udaipur', 'name_hi': 'उदयपुर', 'is_capital': False, 'districts': ['Gomati']},
                {'name': 'Dharmanagar', 'name_hi': 'धर्मनगर', 'is_capital': False, 'districts': ['North Tripura']},
            ]
        },
        'Uttar Pradesh': {
            'code': 'UP',
            'name_hi': 'उत्तर प्रदेश',
            'cities': [
                {'name': 'Lucknow', 'name_hi': 'लखनऊ', 'is_capital': True, 'districts': ['Lucknow', 'Unnao']},
                {'name': 'Kanpur', 'name_hi': 'कानपुर', 'is_capital': False, 'districts': ['Kanpur Nagar', 'Kanpur Dehat']},
                {'name': 'Varanasi', 'name_hi': 'वाराणसी', 'is_capital': False, 'districts': ['Varanasi', 'Chandauli']},
                {'name': 'Prayagraj', 'name_hi': 'प्रयागराज', 'is_capital': False, 'districts': ['Prayagraj', 'Kaushambi']},
                {'name': 'Agra', 'name_hi': 'आगरा', 'is_capital': False, 'districts': ['Agra', 'Firozabad']},
                {'name': 'Meerut', 'name_hi': 'मेरठ', 'is_capital': False, 'districts': ['Meerut', 'Baghpat']},
                {'name': 'Bareilly', 'name_hi': 'बरेली', 'is_capital': False, 'districts': ['Bareilly', 'Pilibhit']},
                {'name': 'Aligarh', 'name_hi': 'अलीगढ़', 'is_capital': False, 'districts': ['Aligarh', 'Hathras']},
                {'name': 'Moradabad', 'name_hi': 'मोरादाबाद', 'is_capital': False, 'districts': ['Moradabad', 'Rampur']},
                {'name': 'Saharanpur', 'name_hi': 'सहारनपुर', 'is_capital': False, 'districts': ['Saharanpur', 'Shamli']},
            ]
        },
        'Uttarakhand': {
            'code': 'UK',
            'name_hi': 'उत्तराखंड',
            'cities': [
                {'name': 'Dehradun', 'name_hi': 'देहरादून', 'is_capital': True, 'districts': ['Dehradun']},
                {'name': 'Haridwar', 'name_hi': 'हरिद्वार', 'is_capital': False, 'districts': ['Haridwar']},
                {'name': 'Rishikesh', 'name_hi': 'ऋषिकेश', 'is_capital': False, 'districts': ['Dehradun']},
                {'name': 'Nainital', 'name_hi': 'नैनीताल', 'is_capital': False, 'districts': ['Nainital', 'Almora']},
                {'name': 'Mussoorie', 'name_hi': 'मसूरी', 'is_capital': False, 'districts': ['Dehradun']},
            ]
        },
        'West Bengal': {
            'code': 'WB',
            'name_hi': 'पश्चिम बंगाल',
            'cities': [
                {'name': 'Kolkata', 'name_hi': 'कोलकाता', 'is_capital': True, 'districts': ['Kolkata', 'North 24 Parganas']},
                {'name': 'Howrah', 'name_hi': 'हावड़ा', 'is_capital': False, 'districts': ['Howrah']},
                {'name': 'Durgapur', 'name_hi': 'दुर्गापुर', 'is_capital': False, 'districts': ['Paschim Bardhaman']},
                {'name': 'Asansol', 'name_hi': 'आसनसोल', 'is_capital': False, 'districts': ['Paschim Bardhaman']},
                {'name': 'Siliguri', 'name_hi': 'सिलीगुड़ी', 'is_capital': False, 'districts': ['Darjeeling', 'Jalpaiguri']},
                {'name': 'Malda', 'name_hi': 'मालदा', 'is_capital': False, 'districts': ['Malda', 'Dakshin Dinajpur']},
            ]
        },
        # Union Territories
        'Andaman and Nicobar Islands': {
            'code': 'AN',
            'name_hi': 'अंडमान और निकोबार द्वीप',
            'cities': [
                {'name': 'Port Blair', 'name_hi': 'पोर्ट ब्लेयर', 'is_capital': True, 'districts': ['South Andaman']},
                {'name': 'Diglipur', 'name_hi': 'डिगलीपुर', 'is_capital': False, 'districts': ['North and Middle Andaman']},
            ]
        },
        'Chandigarh': {
            'code': 'CH',
            'name_hi': 'चंडीगढ़',
            'cities': [
                {'name': 'Chandigarh', 'name_hi': 'चंडीगढ़', 'is_capital': True, 'districts': ['Chandigarh']},
            ]
        },
        'Dadra and Nagar Haveli and Daman and Diu': {
            'code': 'DN',
            'name_hi': 'दादरा और नगर हवेली और दमन और दीव',
            'cities': [
                {'name': 'Daman', 'name_hi': 'दमन', 'is_capital': True, 'districts': ['Daman']},
                {'name': 'Silvassa', 'name_hi': 'सिलवासा', 'is_capital': False, 'districts': ['Dadra and Nagar Haveli']},
                {'name': 'Diu', 'name_hi': 'दीव', 'is_capital': False, 'districts': ['Diu']},
            ]
        },
        'Delhi': {
            'code': 'DL',
            'name_hi': 'दिल्ली',
            'cities': [
                {'name': 'New Delhi', 'name_hi': 'नई दिल्ली', 'is_capital': True, 'districts': ['New Delhi', 'South Delhi']},
                {'name': 'Central Delhi', 'name_hi': 'मध्य दिल्ली', 'is_capital': False, 'districts': ['Central Delhi', 'North Delhi']},
                {'name': 'East Delhi', 'name_hi': 'पूर्वी दिल्ली', 'is_capital': False, 'districts': ['East Delhi', 'Shahdara']},
                {'name': 'West Delhi', 'name_hi': 'पश्चिमी दिल्ली', 'is_capital': False, 'districts': ['West Delhi']},
                {'name': 'Dwarka', 'name_hi': 'द्वारका', 'is_capital': False, 'districts': ['South West Delhi']},
                {'name': 'Rohini', 'name_hi': 'रोहिणी', 'is_capital': False, 'districts': ['North West Delhi']},
            ]
        },
        'Jammu and Kashmir': {
            'code': 'JK',
            'name_hi': 'जम्मू और कश्मीर',
            'cities': [
                {'name': 'Srinagar', 'name_hi': 'श्रीनगर', 'is_capital': True, 'districts': ['Srinagar', 'Ganderbal']},
                {'name': 'Jammu', 'name_hi': 'जम्मू', 'is_capital': False, 'districts': ['Jammu', 'Samba']},
                {'name': 'Anantnag', 'name_hi': 'अनंतनाग', 'is_capital': False, 'districts': ['Anantnag', 'Kulgam']},
                {'name': 'Baramulla', 'name_hi': 'बारामूला', 'is_capital': False, 'districts': ['Baramulla', 'Kupwara']},
                {'name': 'Udhampur', 'name_hi': 'उधमपुर', 'is_capital': False, 'districts': ['Udhampur', 'Reasi']},
            ]
        },
        'Ladakh': {
            'code': 'LA',
            'name_hi': 'लद्दाख',
            'cities': [
                {'name': 'Leh', 'name_hi': 'लेह', 'is_capital': True, 'districts': ['Leh']},
                {'name': 'Kargil', 'name_hi': 'कारगिल', 'is_capital': False, 'districts': ['Kargil']},
            ]
        },
        'Lakshadweep': {
            'code': 'LD',
            'name_hi': 'लक्षद्वीप',
            'cities': [
                {'name': 'Kavaratti', 'name_hi': 'कवरत्ती', 'is_capital': True, 'districts': ['Lakshadweep']},
                {'name': 'Agatti', 'name_hi': 'अगत्ती', 'is_capital': False, 'districts': ['Lakshadweep']},
            ]
        },
        'Puducherry': {
            'code': 'PY',
            'name_hi': 'पुदुचेरी',
            'cities': [
                {'name': 'Puducherry', 'name_hi': 'पुदुचेरी', 'is_capital': True, 'districts': ['Puducherry']},
                {'name': 'Karaikal', 'name_hi': 'करैकल', 'is_capital': False, 'districts': ['Karaikal']},
                {'name': 'Yanam', 'name_hi': 'यानम', 'is_capital': False, 'districts': ['Yanam']},
                {'name': 'Mahe', 'name_hi': 'माहे', 'is_capital': False, 'districts': ['Mahe']},
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
                'name_hi': state_data['name_hi'],
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
                    'name_hi': city_data['name_hi'],
                    'is_capital': city_data['is_capital'],
                }
            )
            if city_created:
                total_cities += 1
            
            for district_name in city_data['districts']:
                district, district_created = District.objects.get_or_create(
                    city=city,
                    name=district_name,
                    defaults={}
                )
                if district_created:
                    total_districts += 1
    
    print(f"Location data created:")
    print(f"  - States/UTs: {total_states}")
    print(f"  - Cities: {total_cities}")
    print(f"  - Districts: {total_districts}")


def create_category_data():
    """Create sample category data."""
    print("\nCreating category data...")
    
    categories = [
        {'name': 'Textile', 'name_hi': 'कपड़ा', 'description': 'Textile and fabric manufacturing'},
        {'name': 'Automotive', 'name_hi': 'ऑटोमोटिव', 'description': 'Automotive parts and manufacturing'},
        {'name': 'Electronics', 'name_hi': 'इलेक्ट्रॉनिक्स', 'description': 'Electronics and technology'},
        {'name': 'Pharmaceuticals', 'name_hi': 'फार्मास्यूटिकल्स', 'description': 'Pharmaceutical and healthcare'},
        {'name': 'Food Processing', 'name_hi': 'खाद्य प्रसंस्करण', 'description': 'Food and beverage processing'},
        {'name': 'Chemicals', 'name_hi': 'रसायन', 'description': 'Chemical manufacturing'},
        {'name': 'Metal Works', 'name_hi': 'धातु कार्य', 'description': 'Metal fabrication and works'},
        {'name': 'Plastics', 'name_hi': 'प्लास्टिक', 'description': 'Plastic manufacturing and products'},
    ]
    
    for cat_data in categories:
        Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'name_hi': cat_data['name_hi'],
                'description': cat_data['description'],
                'slug': cat_data['name'].lower().replace(' ', '-')
            }
        )
    
    print(f"Created {len(categories)} categories")


def create_factory_data(user):
    """Create sample factory data."""
    print("\nCreating factory data...")
    
    try:
        category = Category.objects.first()
        if not category:
            print("No categories found. Run create_category_data() first.")
            return
        
        district = District.objects.first()
        if not district:
            print("No districts found. Run create_location_data() first.")
            return
        
        factories = [
            {
                'name': 'ABC Textiles Pvt Ltd',
                'name_hi': 'एबीसी टेक्सटाइल्स प्राइवेट लिमिटेड',
                'description': 'Leading textile manufacturer specializing in cotton fabrics and garments.',
                'description_hi': 'कपड़ा और परिधान में विशेषज्ञता प्राप्त प्रमुख कपड़ा निर्माता।',
                'category': category,
                'district': district,
                'address': 'Plot No. 123, MIDC Industrial Area, Mumbai',
                'contact_number': '+91 9876543211',
                'contact_email': 'info@abctextiles.com',
                'website': 'https://abctextiles.com',
                'established_year': 2005,
                'employee_count': 250,
                'owner': user,
            },
            {
                'name': 'XYZ Automotive Components',
                'name_hi': 'XYZ ऑटोमोटिव घटक',
                'description': 'Precision automotive parts manufacturer for leading car companies.',
                'description_hi': 'प्रमुख कार कंपनियों के लिए सटीक ऑटोमोटिव पुर्जे निर्माता।',
                'category': category,
                'district': district,
                'address': 'Survey No. 456, Industrial Estate, Pune',
                'contact_number': '+91 9876543212',
                'contact_email': 'contact@xyzauto.com',
                'website': 'https://xyzauto.com',
                'established_year': 2010,
                'employee_count': 180,
                'owner': user,
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
        factory = Factory.objects.first()
        if not factory:
            print("No factories found. Run create_factory_data() first.")
            return
        
        workers = [
            {
                'name': 'Rajesh Kumar',
                'name_hi': 'राजेश कुमार',
                'father_name': 'Mohan Kumar',
                'father_name_hi': 'मोहन कुमार',
                'aadhar_number': '123456789012',
                'mobile': '+91 9876543213',
                'address': 'Room No. 12, Worker Colony, Mumbai',
                'date_of_birth': '1985-05-15',
                'gender': 'Male',
                'education': '10th Pass',
                'education_hi': '10वीं पास',
                'experience': '8 years',
                'experience_hi': '8 साल',
                'skills': 'Machine Operation, Quality Control',
                'skills_hi': 'मशीन संचालन, गुणवत्ता नियंत्रण',
                'factory': factory,
            },
            {
                'name': 'Sunita Devi',
                'name_hi': 'सुनीता देवी',
                'father_name': 'Ram Prasad',
                'father_name_hi': 'राम प्रसाद',
                'aadhar_number': '123456789013',
                'mobile': '+91 9876543214',
                'address': 'Room No. 15, Worker Colony, Mumbai',
                'date_of_birth': '1990-08-20',
                'gender': 'Female',
                'education': '12th Pass',
                'education_hi': '12वीं पास',
                'experience': '5 years',
                'experience_hi': '5 साल',
                'skills': 'Assembly, Packaging',
                'skills_hi': 'असेंबली, पैकेजिंग',
                'factory': factory,
            },
        ]
        
        for worker_data in workers:
            Worker.objects.get_or_create(
                name=worker_data['name'],
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
                    <p>FactoryInfoHub offers a comprehensive platform for exploring India's manufacturing landscape. Here's how to make the most of it:</p>
                    
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
    """Create sample FAQ data."""
    print("\nCreating FAQ data...")
    
    try:
        # Create FAQ categories
        categories = [
            {'name': 'General', 'name_hi': 'सामान्य', 'description': 'General questions about FactoryInfoHub'},
            {'name': 'For Manufacturers', 'name_hi': 'निर्माताओं के लिए', 'description': 'Questions for factory owners and manufacturers'},
            {'name': 'For Buyers', 'name_hi': 'खरीदारों के लिए', 'description': 'Questions for buyers and purchasers'},
        ]
        
        faq_categories = []
        for cat_data in categories:
            cat, created = FAQCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'name_hi': cat_data['name_hi'],
                    'description': cat_data['description'],
                    'slug': cat_data['name'].lower().replace(' ', '-')
                }
            )
            faq_categories.append(cat)
        
        # Create FAQs
        faqs = [
            {
                'question': 'What is FactoryInfoHub?',
                'question_hi': 'FactoryInfoHub क्या है?',
                'answer': 'FactoryInfoHub is a comprehensive platform that provides information about manufacturing units across India, including their capabilities, workforce, and contact details.',
                'answer_hi': 'FactoryInfoHub एक व्यापक मंच है जो भारत भर में विनिर्माण इकाइयों के बारे में जानकारी प्रदान करता है, जिसमें उनकी क्षमताएं, कार्यबल और संपर्क विवरण शामिल हैं।',
                'category': faq_categories[0],
                'order': 1,
            },
            {
                'question': 'How can I register my factory?',
                'question_hi': 'मैं अपनी फैक्ट्री कैसे पंजीकृत कर सकता हूं?',
                'answer': 'You can register your factory by creating an account on FactoryInfoHub and submitting your factory details through the registration form. Our team will verify the information before publishing.',
                'answer_hi': 'आप FactoryInfoHub पर खाता बनाकर और पंजीकरण फ़ॉर्म के माध्यम से अपनी फैक्ट्री का विवरण जमा करके अपनी फैक्ट्री पंजीकृत कर सकते हैं। प्रकाशित करने से पहले हमारी टीम जानकारी की पुष्टि करेगी।',
                'category': faq_categories[1],
                'order': 2,
            },
            {
                'question': 'Is it free to use FactoryInfoHub?',
                'question_hi': 'FactoryInfoHub का उपयोग करना मुफ्त है?',
                'answer': 'Yes, basic usage of FactoryInfoHub is completely free. We offer premium features for manufacturers who want enhanced visibility and additional tools.',
                'answer_hi': 'हाँ, FactoryInfoHub का बुनियादी उपयोग पूरी तरह से मुफ्त है। हम उन निर्माताओं के लिए प्रीमियम सुविधाएं प्रदान करते हैं जो बेहतर दृश्यता और अतिरिक्त उपकरण चाहते हैं।',
                'category': faq_categories[2],
                'order': 3,
            },
        ]
        
        for faq_data in faqs:
            FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
        
        print(f"Created {len(faqs)} FAQs in {len(faq_categories)} categories")
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