from django.db import models
from django.contrib.auth.models import User, AbstractUser





# USER Model (Kế thừa từ AbstractUser để sử dụng sẵn authentication của Django)
class User(AbstractUser):
    balance = models.DecimalField(max_digits=16, decimal_places=0, default=0)

    def __str__(self):  
        return self.username