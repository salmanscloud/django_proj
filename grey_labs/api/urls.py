from django.urls import path
from .views import *

urlpatterns = [
    path('register/', register_user),
    path('login/', login_view, name='login'),
    path('doctors/', DoctorListCreateView.as_view(), name='doctor-list-create'),
    path('doctors/<int:pk>/', doctor_detail, name='doctor-detail'),
    path('patients/', PatientListCreateView.as_view(), name='patient-list-create'),
    path('patients/<int:pk>/', patient_detail, name='patient-detail'),
    path('patient_records/', PatientRecordListCreateView.as_view(), name='patient-record-list-create'),
    path('patient_records/<int:pk>/', patient_record_detail, name='patient-record-detail'),
     path('departments/', DepartmentListCreateView.as_view(), name='department-list-create'),
      path('department/<int:pk>/doctors/', department_doctors, name='department-doctors'),
       path('department/<int:pk>/patients/', department_patients, name='department-patients'),
       path('logout/', logout, name='logout'),
   
    
]
