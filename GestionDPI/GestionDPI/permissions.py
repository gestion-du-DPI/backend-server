from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Custom permission to only allow admins to access the view.
    """
    def has_permission(self, request, view):
        # Check if the user's role is 'Admin'
        if request.user.is_authenticated and request.user.appuser.role == 'Admin':
            return True
        return False
      
class IsPatient(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.appuser.role == 'Patient':
            return True
        return False
      
class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.appuser.role == 'Doctor':
            return True
        return False
      
class IsRadiologist(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.appuser.role == 'Radiologist':
            return True
        return False
      
class IsLabTechnician(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.appuser.role == 'LabTechnician':
            return True
        return False      

class IsLabNurse(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.appuser.role == 'Nurse':
            return True
        return False      
            