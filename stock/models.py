from django.db import models
from django.conf import settings

class StationeryItem(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    total_stock = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveIntegerField(default=10)

    def __str__(self):
        return self.name

class StationeryRequest(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('HOD_Approved', 'HOD Approved'),
        ('Principal_Approved', 'Principal Approved'),
        ('CEO_Approved', 'CEO Approved'),
        ('Rejected', 'Rejected'),
        ('Issued', 'Issued'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(StationeryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='approved_requests', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.user.username} - {self.item.name} ({self.quantity}) - {self.status}"
