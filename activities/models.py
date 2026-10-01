from django.core.exceptions import ValidationError
from django.db import models
from core.models import BaseModel


class Activity(BaseModel):
    date = models.DateField()
    application = models.CharField(max_length=100)
    taken_action = models.TextField()
    name_contact = models.CharField(max_length=70)
    telephone_contact = models.CharField(max_length=20)
    state_validity = models.CharField(max_length=20, default='PENDING')
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
        related_name='activities',
        null=True,
        blank=True  # Commitment es opcional
    )

    def __str__(self):
        return f"{self.date} – {self.application}"


class Evidence(BaseModel):
    class Validity(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    name = models.CharField(max_length=50)
    author = models.CharField(max_length=50)
    date_evidence = models.DateField()
    metadata = models.CharField(max_length=500)
    validity_state = models.CharField(
        max_length=20,
        choices=Validity.choices,
        default=Validity.PENDING,
    )
    date_validity = models.DateField(null=True, blank=True)
    observations_validity = models.TextField(blank=True)

    verificator = models.ForeignKey(
        'personal.Functionary',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
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

    def clean(self):
        super().clean()
        if self.verificator_id and self.verificator_id == self.funcionary_id:
            raise ValidationError(
                {'verificator': 'El verificador no puede ser quien subió la evidencia.'}
            )

    def __str__(self):
        return self.name