from django.db import models


class DSR(models.Model):
    raw_file = models.FileField(upload_to='uploads/')
    date_of_generation = models.DateTimeField(auto_now_add=True)
    remarks = models.CharField(max_length=500)
    original_name = models.CharField(max_length=255, null=True, blank=True)
    special_remarks = models.CharField(max_length=500, null=True, blank=True)
    total_qty_sold = models.IntegerField(default=0)
    total_amount_template = models.FloatField(default=0.0)
    total_amount_raw = models.FloatField(default=0.0)

    uploader = models.CharField(max_length=200)
    extracted_data = models.JSONField(null=True)
    instance = models.CharField(max_length=100)
    chain = models.CharField(max_length=100)
    database = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.original_name

    class Meta:
        ordering = ['-date_of_generation']

class Validation(models.Model):
    generated_file = models.FileField(upload_to='validation/')
    date_of_comparison = models.DateTimeField(auto_now_add=True)
    original_name = models.CharField(max_length=255, null=True, blank=True)
    data_from_generated_file = models.JSONField(null=True)
    instance = models.CharField(max_length=100, null=True, blank=True)


    def __str__(self):
        return self.original_name

    class Meta:
        ordering = ['-date_of_comparison']