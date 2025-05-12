from django.db import models
from django.contrib.auth.models import User

# Create your models here.


#url shortener model  
class UrlShortener(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    short_url = models.CharField(max_length=100)
    long_url = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    count = models.IntegerField(default=0)
    expiration_time = models.DateTimeField(null=True, blank=True)
    qr_code = models.ImageField(null=True, blank=True)
    
    
    def __str__(self):
        return self.short_url