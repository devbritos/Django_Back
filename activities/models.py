from django.db import models
from core.models import BaseModel

# Create your models here.
class Activity(BaseModel):
    date = models.DateField()
    application = models.CharField(max_length=100)
    taken_action = models.TextField()
    name_contact = models.CharField(max_length=70)
    telephone_contact = models.CharField(max_length=20)
    state_validity = models.CharField(max_length=20)
    functionary = models.ForeignKey(
        'personal.Functionary',
        on_delete=models.PROTECT
    )
    measuring = models.ForeignKey(
        'configuration.Measuring',
        on_delete=models.PROTECT
    )
    commitment = models.ForeignKey(
        'agenda.Commitment',
        on_delete=models.PROTECT,
        related_name = 'activities',
        null = True,
        blank = True #Commitment its optional
    )

class Evidence(BaseModel):
    name = models.CharField(max_length=50)
    author = models.CharField(max_length=50)
    date_evidence = models.DateField()
    metadata = models.CharField(max_length=500)
    validity_state = models.CharField(max_length=20)
    date_validity = models.DateField()
    observations_validity = models.TextField()
    
    verificator = models.ForeignKey(
        'personal.Functionary',
        on_delete=models.PROTECT,
        null = True,
        blank = True,
        related_name='evidences_verified',
    )
    activity = models.ForeignKey(
        'activities.Activity',
        on_delete=models.PROTECT,
        related_name='evidences'


    )
    funcionary = models.ForeignKey(
        'personal.Functionary',
        on_delete=models.PROTECT,
        related_name='evidences_uploaded',
    )