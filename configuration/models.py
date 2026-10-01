from django.core.exceptions import ValidationError
from django.db import models
from core.models import BaseModel


class Period(BaseModel):
    start_date = models.DateField()
    end_date = models.DateField()
    computable_days = models.IntegerField()
    status = models.BooleanField(default=True)
    version_parameter = models.CharField(max_length=10)
    minimum_threshold = models.IntegerField()
    maximum_computable_days = models.IntegerField()
    semaphore = models.CharField(max_length=10)

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": "La fecha de término no puede ser anterior a la de inicio."}
            )

    def __str__(self):
        return f"{self.start_date} – {self.end_date}"


class Measuring(BaseModel):
    service = models.CharField(max_length=100)
    measurable_item = models.CharField(max_length=100)
    validity = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.service} – {self.measurable_item}"


class Goal(BaseModel):
    target_value = models.CharField(max_length=100)
    unity = models.CharField(max_length=50)
    goal_value = models.FloatField()
    validity = models.BooleanField(default=True)

    position = models.ForeignKey(
        'personal.Position',
        on_delete=models.PROTECT
    )

    period = models.ForeignKey(
        'Period',
        on_delete=models.PROTECT
    )

    measuring = models.ForeignKey(
        'Measuring',
        on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.position} · {self.measuring} · {self.period}"