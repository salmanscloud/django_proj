from rest_framework.permissions import BasePermission

class IsDoctorInSameDepartment(BasePermission):
    def has_permission(self, request, view):
        # Only allow access if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Only allow access if the user is a doctor
        try:
            doctor = request.user.doctor_profile
        except AttributeError:
            return False

        # Check if the user is in the same department as the records
        if request.method in ['GET', 'POST']:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Ensure the doctor and patient are in the same department
        try:
            doctor = request.user.doctor_profile
        except AttributeError:
            return False
        
        return doctor.department == obj.department
