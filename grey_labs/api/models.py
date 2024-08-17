from django.db import models

# Create your models here.


from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=100)
    diagnostics = models.TextField()
    location = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    department = models.ForeignKey(Department, related_name='doctors', on_delete=models.CASCADE)

    def __str__(self):
        return f'Dr. {self.user.username} - {self.department.name}'

class PatientRecordNew(models.Model):
    record_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(User, related_name='patient_records_new', on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, related_name='patient_records_new', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    diagnostics = models.TextField()
    observations = models.TextField()
    treatments = models.TextField()
    department = models.ForeignKey(Department, related_name='patient_records_new', on_delete=models.CASCADE)
    misc = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Record {self.record_id} for {self.patient.username}'

class DoctorPatientRelationship(models.Model):
    doctor = models.ForeignKey(Doctor, related_name='doctor_patient_relationships', on_delete=models.CASCADE)
    patient = models.ForeignKey(User, related_name='doctor_patient_relationships', on_delete=models.CASCADE)

    def __str__(self):
        return f'Doctor {self.doctor.user.username} - Patient {self.patient.username}'
