#type ignore
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied
from .models import Department, Doctor, DoctorPatientRelationship, PatientRecordNew
from .serializers import UserSerializer, DoctorSerializer, PatientRecordNewSerializer, DepartmentSerializer,UserRegistrationSerializer
from .permissions import IsDoctorInSameDepartment


# doctor or patients register Create newuser

@api_view(['POST'])
def register_user(request):
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
input
post:
{
    "username": "doctor1",
    "password": "securepassword123",
    "email": "doctor1@example.com",
    "group": "Doctors",
    "department": 1  
}
{
    "username": "patient2",
    "password": "securepassword123",
    "email": "patient2@example.com",
    "group": "Patients",
    "doctor": 1  
}

"""

#login Get access token


@api_view(['GET', 'POST'])
def login_view(request):
    if request.method == 'GET':
        return Response({"detail": "Use POST method to authenticate"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if request.method == 'POST':
        data = request.data
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return Response({"error": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

"""
input:
post:{
  "username": "doctor1",
    "password": "securepassword123",
}
"""

# # to get all doctors list ids and names

class IsDoctor(permissions.BasePermission):
    """
    Custom permission to only allow users in the 'Doctors' group.
    """
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Doctors').exists()

class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def list(self, request, *args, **kwargs):
        # Override list method to return only IDs and names
        queryset = self.get_queryset()
        data = [{'id': doctor.user.id, 'name': doctor.user.username} for doctor in queryset]
        return Response(data)


"""
get: list of doctors
for post 
{
    "username": "dr_new",
    "email": "dr_new@example.com",
    "password": "password123",
    "department": 1  
}
"""

# to get particular doctor details


@api_view(['GET', 'PUT', 'DELETE'])
def doctor_detail(request, pk):
    try:
        doctor = Doctor.objects.get(pk=pk)
    except Doctor.DoesNotExist:
        return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if the current user is the doctor whose profile is being accessed
    if request.user != doctor.user:
        raise PermissionDenied("You do not have permission to access this profile.")

    if request.method == 'GET':
        serializer = DoctorSerializer(doctor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = DoctorSerializer(doctor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        doctor.user.delete()  # Optionally delete the associated user as well
        doctor.delete()
        return Response({'message': 'Doctor profile deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

"""
get:particular id 

Put:
{
    "username": "doctor-3",
    "email": "dr_new@example.com",
    "password": "password123",
    "department": 1  
}"""


# to get all patients list id and name


class PatientListCreateView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return all users who are patients associated with any doctor
        return User.objects.filter(doctor_patient_relationships__isnull=False).distinct()

    def perform_create(self, serializer):
        # Create the new user (patient)
        user = serializer.save()

        # Create the relationship with the authenticated doctor
        DoctorPatientRelationship.objects.create(
            doctor=self.request.user.doctor_profile,
            patient=user
        )

        # Create a new patient record in the PatientRecordNew table
        # Assuming you have default or placeholder values for the fields
        PatientRecordNew.objects.create(
            patient=user,
            doctor=self.request.user.doctor_profile,
            diagnostics="Initial diagnostics",
            observations="Initial observations",
            treatments="Initial treatments",
            department=self.request.user.doctor_profile.department,
            misc="No additional information"
        )


# to get particular patient id


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def patient_detail(request, pk):
    # Fetch the patient user object
    patient = get_object_or_404(User, pk=pk)

    # Check if the requesting user is either the patient or a relevant doctor
    if request.user != patient and not DoctorPatientRelationship.objects.filter(
        doctor=request.user.doctor_profile,
        patient=patient
    ).exists():
        raise PermissionDenied("You do not have permission to access this patient.")

    if request.method == 'GET':
        serializer = UserSerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = UserSerializer(patient, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        patient.delete()
        return Response({'message': 'Patient deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

"""

get: particular id
put:
{
    "username": "updated_username",
    "email": "updatedemail@example.com",
    "password": "newpassword123"
}
"""
#  to get all patient records 


class PatientRecordListCreateView(generics.ListCreateAPIView):
    serializer_class = PatientRecordNewSerializer
    permission_classes = [IsAuthenticated, IsDoctorInSameDepartment]

    def get_queryset(self):
        user = self.request.user
        try:
            doctor = user.doctor_profile
        except AttributeError:
            return PatientRecordNew.objects.none()  # Return empty queryset if user is not a doctor
        
        return PatientRecordNew.objects.filter(department=doctor.department)

    def perform_create(self, serializer):
        user = self.request.user
        try:
            doctor = user.doctor_profile
        except AttributeError:
            raise PermissionDenied("You do not have permission to create records.")
        
        # Automatically set the doctor and department based on the authenticated user
        serializer.save(doctor=doctor, department=doctor.department)


"""
get same department records
post:
{
    "patient": 21,
    "diagnostics": "Routine check-up results",
    "observations": "No significant issues found",
    "treatments": "Prescribed vitamins",
    "misc": "Patient requested a follow-up appointment"
}
"""

# to get particular patient records


@api_view(['GET', 'PUT', 'DELETE'])
def patient_record_detail(request, pk):
    try:
        record = PatientRecordNew.objects.get(pk=pk)
    except PatientRecordNew.DoesNotExist:
        return Response({'detail': 'Record not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the current user is the patient or the doctor for this record
    if request.user != record.patient and request.user != record.doctor.user:
        raise PermissionDenied("You do not have permission to access this record.")

    if request.method == 'GET':
        serializer = PatientRecordNewSerializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = PatientRecordNewSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        record.delete()
        return Response({'message': 'Record deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

"""
put:
{
    "diagnostics": "Updated diagnostics",
    "observations": "Updated observations"
}

"""


# to get all departments


class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

"""
get all data
post:
{
    "name": "Cardiology",
    "diagnostics": "Heart-related diagnostics",
    "location": "Building A, Floor 2",
    "specialization": "Cardiovascular diseases"
}
"""

# to get all doctors in particular departments



@api_view(['GET', 'PUT'])
def department_doctors(request, pk):
    # Retrieve the department
    department = get_object_or_404(Department, pk=pk)

    # Check if the current user is a doctor in this department
    try:
        doctor = request.user.doctor_profile
    except AttributeError:
        return Response({'detail': 'User is not a doctor'}, status=status.HTTP_403_FORBIDDEN)

    if doctor.department != department:
        raise PermissionDenied("You do not have permission to access doctors in this department.")

    if request.method == 'GET':
        doctors = Doctor.objects.filter(department=department)
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        # This method allows updating doctor details. Ensure to handle updates appropriately.
        # Here, we assume that the request data includes doctor IDs to update or other necessary data.
        data = request.data

        # Note: Actual implementation would depend on what fields are being updated and how
        # We will need to handle updating doctor instances based on the provided data

        # Example: Updating a specific doctor
        for doctor_data in data:
            doctor_id = doctor_data.get('id')
            try:
                doctor = Doctor.objects.get(pk=doctor_id, department=department)
                serializer = DoctorSerializer(doctor, data=doctor_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Doctor.DoesNotExist:
                return Response({'detail': f'Doctor with ID {doctor_id} not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'detail': 'Doctors updated successfully'}, status=status.HTTP_200_OK)


"""
get all doctor in same department

put:
[
    {
        "id": 1,
        "username": "updated_doctor1",
        "email": "updated_doctor1@example.com"
    },
    {
        "id": 2,
        "username": "updated_doctor2",
        "email": "updated_doctor2@example.com"
    }
]"""


# to get all patients in particular department




@api_view(['GET', 'PUT'])
def department_patients(request, pk):
    # Retrieve the department
    department = get_object_or_404(Department, pk=pk)

    # Check if the current user is a doctor in this department
    try:
        doctor = request.user.doctor_profile
    except AttributeError:
        return Response({'detail': 'User is not a doctor'}, status=status.HTTP_403_FORBIDDEN)

    if doctor.department != department:
        raise PermissionDenied("You do not have permission to access patients in this department.")

    if request.method == 'GET':
        # Get all patients in the specified department
        patient_ids = DoctorPatientRelationship.objects.filter(doctor=doctor).values_list('patient_id', flat=True)
        patients = User.objects.filter(id__in=patient_ids)
        serializer = UserSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        # Update patient details
        data = request.data
        updated_count = 0

        for patient_data in data:
            patient_id = patient_data.get('id')
            try:
                patient = User.objects.get(pk=patient_id)
                # Ensure the patient is in the same department
                if not DoctorPatientRelationship.objects.filter(patient=patient, doctor=doctor).exists():
                    return Response({'detail': f'Patient with ID {patient_id} is not associated with this doctor.'}, status=status.HTTP_400_BAD_REQUEST)
                
                serializer = UserSerializer(patient, data=patient_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated_count += 1
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'detail': f'Patient with ID {patient_id} not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'detail': f'{updated_count} patients updated successfully'}, status=status.HTTP_200_OK)


"""

put:
[
    {
        "id": 1,
        "username": "updated_patient1",
        "email": "updated_patient1@example.com",
        "password": "newpassword123"
    },
    {
        "id": 2,
        "username": "updated_patient2",
        "email": "updated_patient2@example.com",
        "password": "anothernewpassword"
    }
]
"""


# logout


# @api_view(['POST'])
# def logout(request):
#     # Ensure the user is authenticated
#     if not request.user.is_authenticated:
#         return Response({'detail': 'User not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
    
#     # Attempt to delete the user's token
#     try:
#         # Get the user's token
#         token = Token.objects.get(user=request.user)
#         token.delete()  # Delete the token to log out the user
#         return Response({'detail': 'Successfully logged out'}, status=status.HTTP_204_NO_CONTENT)
#     except Token.DoesNotExist:
#         return Response({'detail': 'No token found'}, status=status.HTTP_400_BAD_REQUEST)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        # Get the refresh token from the request data
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Blacklist the refresh token
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
    except TokenError:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)



"""
post:
in header acces token 
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyMzgyNzYyNCwiaWF0IjoxNzIzNzQxMjI0LCJqdGkiOiI0OGU3Mjg2YjgxYTY0NjlmOGYzZThlM2QyYTVjNGUzMiIsInVzZXJfaWQiOjF9.qEoDha5Dfuz9eVSlYW_D7BgK2zMxL31iWVNpT5GqN_0"
}
"""