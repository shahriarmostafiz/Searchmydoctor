from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Doctor, Chamber, Specialization, DoctorSearchIndex


def build_search_doc(doctor: Doctor) -> str:
    parts = []
    parts.append((doctor.full_name or "").strip())

    for sp in doctor.specializations.all():
        parts.append((sp.name or "").strip())

    for ch in doctor.chambers.select_related("hospital").all():
        parts.append((ch.name or "").strip())
        parts.append((ch.city or "").strip())
        parts.append((ch.state or "").strip())
        if ch.hospital:
            parts.append((ch.hospital.name or "").strip())

    lowered = [p.lower() for p in parts if p]
    # dedupe while keeping order
    unique = list(dict.fromkeys(lowered))
    return " ".join(unique)


def reindex_doctor(doctor_id: int):
    doctor = Doctor.objects.filter(id=doctor_id).first()
    if not doctor:
        return
    textdoc = build_search_doc(doctor)
    DoctorSearchIndex.objects.update_or_create(
        doctor=doctor, defaults={"search_text": textdoc}
    )


@receiver(post_save, sender=Doctor)
def doctor_saved(sender, instance, **kwargs):
    reindex_doctor(instance.id)


@receiver(post_save, sender=Chamber)
def chamber_saved(sender, instance, **kwargs):
    reindex_doctor(instance.doctor_id)


@receiver(m2m_changed, sender=Doctor.specializations.through)
def doctor_specs_changed(sender, instance, action, **kwargs):
    if action in ("post_add", "post_remove", "post_clear"):
        reindex_doctor(instance.id)
