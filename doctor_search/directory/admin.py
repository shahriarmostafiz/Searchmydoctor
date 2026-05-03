from django.contrib import admin
from .models import (
    Doctor, Specialization, Hospital,
    Chamber, ChamberSchedule, DoctorSearchIndex
)

class ChamberScheduleInline(admin.TabularInline):
    model = ChamberSchedule
    extra = 1

class ChamberInline(admin.StackedInline):
    model = Chamber
    extra = 1
    show_change_link = True

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "gender", "phone", "email")
    search_fields = ("full_name", "full_name_ci")
    list_filter = ("gender",)
    filter_horizontal = ("specializations",)
    inlines = [ChamberInline]

@admin.register(Chamber)
class ChamberAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "doctor", "city", "state", "is_active")
    search_fields = ("name", "doctor__full_name", "city", "state")
    list_filter = ("state", "city", "is_active")
    inlines = [ChamberScheduleInline]

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "state")
    search_fields = ("name", "city", "state")
    list_filter = ("state", "city")

@admin.register(DoctorSearchIndex)
class DoctorSearchIndexAdmin(admin.ModelAdmin):
    list_display = ("doctor", "updated_at")
    search_fields = ("search_text",)
