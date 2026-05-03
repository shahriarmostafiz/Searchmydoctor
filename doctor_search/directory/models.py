from django.db import models
from django.db.models import Q
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True


class Specialization(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class Hospital(TimeStampedModel):
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)

    state = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    city = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["state", "city", "zip_code"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Doctor(TimeStampedModel):
    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    )

    full_name = models.CharField(max_length=150)
    full_name_ci = models.CharField(max_length=150, db_index=True)

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Other")
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=150, blank=True, null=True)

    photo = models.CharField(max_length=255, blank=True, null=True)

    specializations = models.ManyToManyField(Specialization, related_name="doctors", blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["full_name"]),
            models.Index(fields=["full_name_ci"]),
        ]

    def save(self, *args, **kwargs):
        self.full_name_ci = (self.full_name or "").lower().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name


class Chamber(TimeStampedModel):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="chambers")
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name="chambers")

    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)

    state = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    city = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    upazila = models.CharField(max_length=120, blank=True, null=True,db_index=True)
   
    zip_code = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    timezone = models.CharField(max_length=64, default="UTC")
    is_active = models.BooleanField(default=True)

    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["doctor", "name", "address"], name="uq_chamber_doctor_name_address"),
        ]
        indexes = [
            models.Index(fields=["state", "city", "zip_code",'upazila']),
        ]

    def __str__(self):
        return f"{self.name} ({self.doctor.full_name})"


from django.db import models
from django.db.models import Q, F

class ChamberSchedule(TimeStampedModel):
    chamber = models.ForeignKey("Chamber", on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.SmallIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    effective_start_date = models.DateField(blank=True, null=True)
    effective_end_date = models.DateField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(day_of_week__gte=0) & Q(day_of_week__lte=6),
                name="ck_schedule_day_range",
            ),
            models.CheckConstraint(
                check=Q(start_time__lt=F("end_time")),
                name="ck_schedule_start_before_end",
            ),
            models.UniqueConstraint(
                fields=["chamber", "day_of_week", "start_time", "end_time"],
                name="uq_schedule_exact_window",
            ),
        ]
        indexes = [
            models.Index(fields=["day_of_week", "start_time", "end_time"]),
        ]

class DoctorSearchIndex(models.Model):
    """
    Denormalized search text per doctor (fast FULLTEXT/LIKE search).
    Create this as 1:1 with Doctor.
    """
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name="search_index", primary_key=True)
    search_text = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["doctor"]),  # 1:1 anyway
        ]

    def __str__(self):
        return f"SearchIndex({self.doctor_id})"




from django.db import models


class Division(models.Model):
    division_id = models.IntegerField(db_column="DivisionId", primary_key=True)
    division_name = models.CharField(db_column="DivisionName", max_length=100)
    division_bng_name = models.CharField(db_column="DivisionBngName", max_length=200, null=True, blank=True)
    division_url = models.CharField(db_column="DivisionUrl", max_length=50, null=True, blank=True)

    class Meta:
        # managed = False
        db_table = "Division"

    def __str__(self):
        return self.division_name


class District(models.Model):
    district_id = models.IntegerField(db_column="DistrictId", primary_key=True)
    division = models.ForeignKey(
        Division,
        db_column="DivisionId",
        on_delete=models.DO_NOTHING,
        related_name="districts",
    )
    district_name = models.CharField(db_column="DistrictName", max_length=1000, null=True, blank=True)
    district_bng_name = models.CharField(db_column="DistrictBngName", max_length=200, null=True, blank=True)
    latitude = models.FloatField(db_column="Latitude", null=True, blank=True)
    longitude = models.FloatField(db_column="Longitude", null=True, blank=True)
    web_url = models.CharField(db_column="WebUrl", max_length=1000, null=True, blank=True)  # NCHAR(1000)

    class Meta:
        # managed = False
        db_table = "District"

    def __str__(self):
        return self.district_name or f"District {self.district_id}"


class Upazilas(models.Model):
    upazilas_id = models.IntegerField(db_column="UpazilasId", primary_key=True)
    district = models.ForeignKey(
        District,
        db_column="DistrictId",
        on_delete=models.DO_NOTHING,
        related_name="upazilas",
    )
    upazilas_name = models.CharField(db_column="UpazilasName", max_length=25)
    upazilas_bng_name = models.CharField(db_column="UpazilasBngName", max_length=250)
    web_url = models.CharField(db_column="WebUrl", max_length=50)

    class Meta:
        # managed = False
        db_table = "Upazilas"

    def __str__(self):
        return self.upazilas_name


class Union(models.Model):
    union_id = models.IntegerField(db_column="UnionId", primary_key=True)
    upazila = models.ForeignKey(
        Upazilas,
        db_column="UpazilaId",
        on_delete=models.DO_NOTHING,
        related_name="unions",
    )
    union_name = models.CharField(db_column="UnionName", max_length=25)
    union_bng_name = models.CharField(db_column="UnionBngName", max_length=250)
    web_url = models.CharField(db_column="WebUrl", max_length=50)

    class Meta:
        # managed = False
        db_table = "Union"   # if your DB table is still "Uninon", change this to "Uninon"

    def __str__(self):
        return self.union_name



from django.db import models

class Districts(models.Model):
    id = models.AutoField(primary_key=True)
    division = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    thana = models.CharField(max_length=255)
    postoffice = models.CharField(max_length=255)
    postcode = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'districts'   # 👈 important
        managed = False          # 👈 VERY IMPORTANT




from django.db import models


class AllDivisions(models.Model):
    name = models.CharField(max_length=50)
    name_bn = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "all_divisions"
        managed = False


class AllDistricts(models.Model):
    division = models.ForeignKey(AllDivisions, on_delete=models.CASCADE, db_column="division_id")
    name = models.CharField(max_length=50)
    name_bn = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "all_districts"
        managed = False


class AllUpazilas(models.Model):
    district = models.ForeignKey(AllDistricts, on_delete=models.CASCADE, db_column="district_id")
    name = models.CharField(max_length=50)
    name_bn = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "all_upazilas"
        managed = False


class AllThanas(models.Model):
    district = models.ForeignKey(AllDistricts, on_delete=models.CASCADE, db_column="district_id")
    name = models.CharField(max_length=50)
    name_bn = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "all_thanas"
        managed = False