import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestDoctorViews:
    def test_doctor_only_view(self, authenticated_doctor_client, test_consultation):
        """Test DoctorOnlyView returns correct information"""
        url = reverse('doctor_home')
        response = authenticated_doctor_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        doctor_info = data['doctor_info']
        
        # Test basic doctor info
        assert doctor_info['name'] == 'Test Doctor'
        assert doctor_info['email'] == 'doctor1@test.com'
        assert doctor_info['nss'] == '888'
        assert doctor_info['phone_number'] == '123456789'
        
        # Test response structure
        assert 'stats' in data
        assert 'recent_patients' in data
        assert 'requested_tests' in data
        
        # Test recent patients data
        assert len(data['recent_patients']) <= 5  # Should show max 5 recent patients

    def test_get_patients_list(self, authenticated_doctor_client, test_patient):
        """Test GetPatientsList returns correct patient information"""
        url = reverse('patients_list')
        response = authenticated_doctor_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert 'patients' in data
        patients = data['patients']
        
        # Should have at least our test patient
        assert len(patients) >= 1
        
        # Find our test patient in the list
        test_patient_data = next(
            (p for p in patients if p['nss'] == '999'),
            None
        )
        
        assert test_patient_data is not None
        assert test_patient_data['name'] == 'Test Patient'
        assert test_patient_data['email'] == 'patient1@test.com'
        assert test_patient_data['phone_number'] == '987654321'
        assert test_patient_data['emergency_contact_name'] == 'Emergency Contact'
        assert test_patient_data['emergency_contact_phone'] == '112233445'

    def test_unauthorized_access(self, api_client):
        """Test unauthorized access is prevented"""
        # Test DoctorOnlyView
        response = api_client.get(reverse('doctor_home'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test GetPatientsList
        response = api_client.get(reverse('patients_list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED