from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# Create your models here.
class History(models.Model):
    username = models.TextField()
    password = models.TextField()
    auth_token = models.TextField() 
    login_state  = models.TextField()
    configuration  = models.TextField()
    result = models.TextField()
    reservation = models.TextField()
    user = models.ForeignKey(User, default=1,on_delete=models.CASCADE,db_column="user_id")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = 'Snapshots'