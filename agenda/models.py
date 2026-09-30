from django.db import models

from core.models import BaseModel
# Create your models here.

class Commitment(BaseModel):
    STATES_CHOICES = [
        ('JOINED', 'Joined'),
        ('PENDING','Pending'),
        ('IN_PROGRESS','In progress'),
        ('DONE','Done')
    ]

    origin = models.CharField(max_length= 100)
    applic_name = models.CharField(max_length = 70)
    territory = models.CharField(max_length= 60)
    commitment_date =  models.DateField()
    support = models.CharField(max_length= 200, blank = True)
    state = models.CharField(max_length = 20,choices=STATES_CHOICES,default='JOINED')
    observation = models.CharField(max_length = 300, blank = True)

    functionary = models.ForeignKey(
        'personal.Functionary',
        on_delete=models.PROTECT,
        related_name='commitments',
    )

    measuring = models.ForeignKey(
        'configuration.Measuring',
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = 'commitments',
    )



    def __str__(self):
        return f"{self.applic_name} {self.state}"
