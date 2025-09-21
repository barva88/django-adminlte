from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'company_type', 'fleet_size')
    search_fields = ('name', 'owner__username', 'dot', 'mc')
