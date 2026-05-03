from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction


from .models import Doctor, Specialization, Chamber, ChamberSchedule

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url="/login/")(view_func)

def doctor_search_page(request):
    # Public landing page
    return render(request, "ui/search/search.html")

@superuser_required
def admin_dashboard(request):
    return render(request, "ui/admin/dashboard.html")

@superuser_required
def doctor_list_ui(request):
    doctors = Doctor.objects.all().order_by("full_name_ci").prefetch_related("specializations", "chambers")
    return render(request, "ui/doctors/list.html", {"doctors": doctors})

@superuser_required
@transaction.atomic


def doctor_create_ui(request):
    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        gender = (request.POST.get("gender") or "Other").strip()
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()

        if not full_name:
            messages.error(request, "Doctor name is required")
            return redirect("doctor_create_ui")

        try:
            with transaction.atomic():
                doctor = Doctor.objects.create(
                    full_name=full_name,
                    gender=gender,
                    phone=phone or None,
                    email=email or None,
                )

                spec_names = request.POST.getlist("specialization_names[]")
                spec_objs = []
                for raw in spec_names:
                    name = (raw or "").strip()
                    if not name:
                        continue
                    sp, _ = Specialization.objects.get_or_create(name=name)
                    spec_objs.append(sp)

                if spec_objs:
                    doctor.specializations.set(spec_objs)

                try:
                    chamber_count = int(request.POST.get("chamber_count") or 0)
                except (TypeError, ValueError):
                    chamber_count = 0

                for i in range(chamber_count):
                    prefix = f"chamber_{i}_"

                    ch_name = (request.POST.get(prefix + "name") or "").strip()
                    ch_address = (request.POST.get(prefix + "address") or "").strip()

                    if not (ch_name and ch_address):
                        continue

                    chamber = Chamber.objects.create(
                        doctor=doctor,
                        name=ch_name,
                        address=ch_address,
                        state=(request.POST.get(prefix + "state") or "").strip() or None,      # division
                        city=(request.POST.get(prefix + "city") or "").strip() or None,        # zilla/district
                        upazila=(request.POST.get(prefix + "upazila") or "").strip() or None,  # upazila/thana
                        zip_code=(request.POST.get(prefix + "zip") or "").strip() or None,
                        phone=(request.POST.get(prefix + "phone") or "").strip() or None,
                        timezone=(request.POST.get(prefix + "timezone") or "Asia/Dhaka").strip(),
                        is_active=True,
                    )

                    try:
                        sched_count = int(request.POST.get(prefix + "sched_count") or 0)
                    except (TypeError, ValueError):
                        sched_count = 0

                    for j in range(sched_count):
                        day = request.POST.get(prefix + f"sched_{j}_day")
                        start = request.POST.get(prefix + f"sched_{j}_start")
                        end = request.POST.get(prefix + f"sched_{j}_end")

                        if not (day and start and end):
                            continue

                        try:
                            day_int = int(day)
                        except (TypeError, ValueError):
                            continue

                        ChamberSchedule.objects.create(
                            chamber=chamber,
                            day_of_week=day_int,
                            start_time=start,
                            end_time=end,
                        )

        except Exception as e:
            messages.error(request, f"Failed to create doctor: {str(e)}")
            return redirect("doctor_create_ui")

        messages.success(request, "Doctor created successfully")
        return redirect("doctor_list_ui")

    specializations = Specialization.objects.all().order_by("name")
    return render(request, "ui/doctors/create.html", {"specializations": specializations})

def doctor_create_ui1(request):
    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        gender = request.POST.get("gender") or "Other"
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()

        if not full_name:
            messages.error(request, "Doctor name is required")
            return redirect("doctor_create_ui")

        doctor = Doctor.objects.create(
            full_name=full_name,
            gender=gender,
            phone=phone or None,
            email=email or None,
        )

        spec_names = request.POST.getlist("specialization_names[]")
        spec_objs = []
        for raw in spec_names:
            name = (raw or "").strip()
            if not name:
                continue
            sp, _ = Specialization.objects.get_or_create(name=name)
            spec_objs.append(sp)
        if spec_objs:
            doctor.specializations.set(spec_objs)

        chamber_count = int(request.POST.get("chamber_count") or 0)
        for i in range(chamber_count):
            prefix = f"chamber_{i}_"
            ch_name = (request.POST.get(prefix + "name") or "").strip()
            ch_address = (request.POST.get(prefix + "address") or "").strip()
            if not (ch_name and ch_address):
                continue

            chamber = Chamber.objects.create(
                doctor=doctor,
                name=ch_name,
                address=ch_address,
                state=(request.POST.get(prefix + "state") or "").strip() or None,
                city=(request.POST.get(prefix + "city") or "").strip() or None,
                zip_code=(request.POST.get(prefix + "zip") or "").strip() or None,
                phone=(request.POST.get(prefix + "phone") or "").strip() or None,
                timezone=(request.POST.get(prefix + "timezone") or "UTC").strip(),
                is_active=True,
            )

            sched_count = int(request.POST.get(prefix + "sched_count") or 0)
            for j in range(sched_count):
                day = request.POST.get(prefix + f"sched_{j}_day")
                start = request.POST.get(prefix + f"sched_{j}_start")
                end = request.POST.get(prefix + f"sched_{j}_end")
                if not (day and start and end):
                    continue

                ChamberSchedule.objects.create(
                    chamber=chamber,
                    day_of_week=int(day),
                    start_time=start,
                    end_time=end,
                )

        messages.success(request, "Doctor created successfully")
        return redirect("doctor_list_ui")

    specializations = Specialization.objects.all().order_by("name")
    return render(request, "ui/doctors/create.html", {"specializations": specializations})



@superuser_required
@transaction.atomic
def doctor_edit_ui(request, doctor_id):
    doctor = get_object_or_404(
        Doctor.objects.prefetch_related("specializations", "chambers__schedules"),
        id=doctor_id,
    )

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        gender = request.POST.get("gender") or "Other"
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()

        if not full_name:
            messages.error(request, "Doctor name is required")
            return redirect("doctor_edit_ui", doctor_id=doctor.id)

        doctor.full_name = full_name
        doctor.gender = gender
        doctor.phone = phone or None
        doctor.email = email or None
        doctor.save()

        spec_names = request.POST.getlist("specialization_names[]")
        spec_objs = []
        for raw in spec_names:
            name = (raw or "").strip()
            if not name:
                continue
            sp, _ = Specialization.objects.get_or_create(name=name)
            spec_objs.append(sp)
        doctor.specializations.set(spec_objs)

        # delete and recreate
        doctor.chambers.all().delete()

        chamber_count = int(request.POST.get("chamber_count") or 0)

        for i in range(chamber_count):
            prefix = f"chamber_{i}_"
            ch_name = (request.POST.get(prefix + "name") or "").strip()
            ch_address = (request.POST.get(prefix + "address") or "").strip()

            if not (ch_name and ch_address):
                continue

            chamber = Chamber.objects.create(
                doctor=doctor,
                name=ch_name,
                address=ch_address,
                state=(request.POST.get(prefix + "state") or "").strip() or None,
                city=(request.POST.get(prefix + "city") or "").strip() or None,
                zip_code=(request.POST.get(prefix + "zip") or "").strip() or None,
                phone=(request.POST.get(prefix + "phone") or "").strip() or None,
                timezone=(request.POST.get(prefix + "timezone") or "UTC").strip(),
                is_active=(request.POST.get(prefix + "is_active", "1") == "1"),
            )

            sched_count = int(request.POST.get(prefix + "sched_count") or 0)
            for j in range(sched_count):
                day = request.POST.get(prefix + f"sched_{j}_day")
                start = request.POST.get(prefix + f"sched_{j}_start")
                end = request.POST.get(prefix + f"sched_{j}_end")

                if not (day and start and end):
                    continue

                ChamberSchedule.objects.create(
                    chamber=chamber,
                    day_of_week=int(day),
                    start_time=start,
                    end_time=end,
                )

        messages.success(request, "Doctor updated successfully")
        return redirect("doctor_list_ui")

    specializations = Specialization.objects.all().order_by("name")
    selected_specs = list(doctor.specializations.values_list("name", flat=True))

    chamber_payload = []
    for chamber in doctor.chambers.prefetch_related("schedules").all().order_by("id"):
        schedules = chamber.schedules.all().order_by("day_of_week", "start_time")
        print("schedules", schedules)
        print("chamber", chamber.id)

        chamber_payload.append({
            "name": chamber.name or "",
            "address": chamber.address or "",
            "state": chamber.state or "",
            "city": chamber.city or "",
            "zip": chamber.zip_code or "",
            "phone": chamber.phone or "",
            "timezone": chamber.timezone or "UTC",
            "is_active": chamber.is_active,
            "schedules": [
                {
                    "day": int(s.day_of_week),
                    "start": s.start_time.strftime("%H:%M") if s.start_time else "",
                    "end": s.end_time.strftime("%H:%M") if s.end_time else "",
                }
                for s in schedules
            ],
        })

    print("CHAMBER PAYLOAD:", chamber_payload)
    # chamber_payload = []
    # for chamber in doctor.chambers.all().order_by("id"):
    #     chamber_payload.append({
    #         "name": chamber.name or "",
    #         "address": chamber.address or "",
    #         "state": chamber.state or "",
    #         "city": chamber.city or "",
    #         "zip": chamber.zip_code or "",
    #         "phone": chamber.phone or "",
    #         "timezone": chamber.timezone or "UTC",
    #         "is_active": chamber.is_active,
    #         "schedules": [
    #             {
    #                 "day": s.day_of_week,
    #                 "start": s.start_time.strftime("%H:%M"),
    #                 "end": s.end_time.strftime("%H:%M"),
    #             }
    #             for s in chamber.schedules.all().order_by("day_of_week", "start_time")
    #         ],
    #     })

    return render(
        request,
        "ui/doctors/edit.html",
        {
            "doctor": doctor,
            "specializations": specializations,
            "selected_specs": selected_specs,
            "chamber_payload": chamber_payload,
        },
    )

