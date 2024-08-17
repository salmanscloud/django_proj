
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import Doctor, DoctorPatientRelationship, Department,PatientRecordNew

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    group = serializers.ChoiceField(choices=[('Doctors', 'Doctors'), ('Patients', 'Patients')])
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=False)  # Only for doctors
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), required=False)  # Only for patients

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'group', 'department', 'doctor')

    def create(self, validated_data):
        group_name = validated_data.pop('group')
        department = validated_data.pop('department', None)
        doctor = validated_data.pop('doctor', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email']
        )
        
        # Add the user to the appropriate group
        group, created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

        if group_name == 'Doctors':
            # If the user is a doctor, ensure a department is provided and create a Doctor record
            if not department:
                raise serializers.ValidationError("Department is required for doctors.")
            Doctor.objects.create(user=user, department=department)

        elif group_name == 'Patients':
            # If the user is a patient, ensure a doctor is provided and create a DoctorPatientRelationship record
            if not doctor:
                raise serializers.ValidationError("A doctor is required for patients.")
            DoctorPatientRelationship.objects.create(doctor=doctor, patient=user)

            PatientRecordNew.objects.create(
                patient=user,
                doctor=doctor,
                diagnostics="Initial diagnosis",  # Can be replaced with actual data if needed
                observations="Initial observation",  # Can be replaced with actual data if needed
                treatments="Initial treatment",  # Can be replaced with actual data if needed
                department=doctor.department,  # Assuming the department is the same as the doctor's
                misc="Miscellaneous information"  # Optional field
            )
        return user

# from rest_framework import serializers
# from django.contrib.auth.models import User
# from .models import Doctor

# class DoctorSerializer(serializers.ModelSerializer):
#     username = serializers.CharField(source='user.username')
#     email = serializers.EmailField(source='user.email')
#     password = serializers.CharField(write_only=True, source='user.password')

#     class Meta:
#         model = Doctor
#         fields = ('id', 'username', 'email', 'password', 'department')

#     def create(self, validated_data):
#         user_data = validated_data.pop('user')
#         password = user_data.pop('password')
#         user = User.objects.create_user(
#             username=user_data['username'],
#             email=user_data['email'],
#             password=password
#         )
#         doctor = Doctor.objects.create(user=user, department=validated_data['department'])
#         return doctor
# from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Doctor

class DoctorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    password = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ('id', 'username', 'email', 'password', 'department')

    def get_password(self, obj):
        # Return a placeholder to indicate a password is set
        return '********'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password = user_data.pop('password')
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=password
        )
        doctor = Doctor.objects.create(user=user, department=validated_data['department'])
        return doctor

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        user.username = user_data.get('username', user.username)
        user.email = user_data.get('email', user.email)
        password = user_data.get('password', None)
        if password:
            user.set_password(password)
        user.save()

        instance.department = validated_data.get('department', instance.department)
        instance.save()

        return instance


from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Create a new user with hashed password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

    def update(self, instance, validated_data):
        # Update the user's details
        username = validated_data.get('username', instance.username)
        email = validated_data.get('email', instance.email)
        password = validated_data.get('password', None)

        instance.username = username
        instance.email = email
        
        if password:
            # Only update password if provided
            instance.set_password(password)
        
        instance.save()
        return instance


from rest_framework import serializers
from .models import PatientRecordNew

class PatientRecordNewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientRecordNew
        fields = ['record_id', 'patient', 'created_date', 'diagnostics', 'observations', 'treatments', 'misc', 'doctor', 'department']
        read_only_fields = ['record_id', 'created_date', 'doctor', 'department']

from rest_framework import serializers
from .models import Department

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'diagnostics', 'location', 'specialization']
