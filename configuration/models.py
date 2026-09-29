from django.db import models
from core.models import BaseModel

# Create your models here.
class Period(BaseModel):
    start_date = models.DateField()
    end_date = models.DateField()
    computable_days = models.IntegerField()
    status = models.BooleanField(default=True)
    version_parameter = models.CharField(max_length=10)
    minimum_threshold = models.IntegerField()
    maximum_computable_days = models.IntegerField()
    semaphore = models.CharField(max_length=10)

class Measuring(BaseModel):
    service = models.CharField(max_length=100)
    measurable_item = models.CharField(max_length=100)
    validity = models.BooleanField(default=True)

class Goal(BaseModel):
    target_value = models.CharField(max_length=100)
    unity = models.CharField(max_length=50)
    goal_value = models.FloatField()
    validity = models.BooleanField(default=True)

    id_cargo = models.ForeignKey(
        'Cargo',
        on_delete=models.PROTECT
    )

    id_period = models.ForeignKey(
        'Period',
        on_delete=models.PROTECT
    )

    id_measuring = models.ForeignKey(
        'Measuring',
        on_delete=models.PROTECT
    )
