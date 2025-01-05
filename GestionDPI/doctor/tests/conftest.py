import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from datetime import datetime
from django.utils.timezone import make_aware
from users.models import AppUser, Patient, Worker
from doctor.models import Consultation, Hospital
import os
from django.conf import settings

@pytest.fixture
def api_client():
    """Base API client fixture"""
    return APIClient()

@pytest.fixture
def test_password():
    """Fixture for test password"""
    return 'test_password123'

@pytest.fixture
def test_hospital(db):
    """Create test hospital"""
    return Hospital.objects.create(
        name="Test Hospital",
       
    )

@pytest.fixture
def test_doctor(db, test_password, test_hospital):
    """Create test doctor with all related objects"""
    # Create User
    user = User.objects.create_user(
        username='testdoctor',
        email='doctor1@test.com',
        password=test_password,
        first_name='Test',
        last_name='Doctor'
    )
    
    # Create AppUser
    app_user = AppUser.objects.create(
        user=user,
        role='Doctor',
        hospital=test_hospital,
        nss='888',
        phone_number='123456789',
        address='Test Address',
        date_of_birth=make_aware(datetime(1980, 1, 1)),
        place_of_birth="alger",
        gender='Male'
    )
    
    # Create Worker
    worker = Worker.objects.create(
        user=app_user,
        speciality='General'
    )
    
    return {
        'user': user,
        'app_user': app_user,
        'worker': worker
    }

@pytest.fixture
def test_patient(db, test_password, test_hospital):
    """Create test patient with all related objects"""
    # Create User
    user = User.objects.create_user(
        username='testpatient',
        email='patient1@test.com',
        password=test_password,
        first_name='Test',
        last_name='Patient'
    )
    
    # Create AppUser
    app_user = AppUser.objects.create(
        user=user,
        role='Patient',
        hospital=test_hospital,
        nss='999',
        phone_number='987654321',
        address='Patient Address',
        date_of_birth=make_aware(datetime(1990, 1, 1)),
        place_of_birth="alger",
        gender='Female'
    )
    
    # Create Patient
    patient = Patient.objects.create(
        user=app_user,
        emergency_contact_name='Emergency Contact',
        emergency_contact_phone='112233445',
        medical_condition="mksor"
    )
    
    return {
        'user': user,
        'app_user': app_user,
        'patient': patient
    }

@pytest.fixture
def authenticated_doctor_client(api_client, test_doctor):
    """Create authenticated doctor client"""
    api_client.force_authenticate(user=test_doctor['user'])
    return api_client

@pytest.fixture
def test_consultation(db, test_doctor, test_patient):
    """Create test consultation"""
    return Consultation.objects.create(
        patient=test_patient['patient'],
        doctor=test_doctor['worker'],
        priority='Low',
        reason='Test consultation',
        archived=False,
        resume=''
    )