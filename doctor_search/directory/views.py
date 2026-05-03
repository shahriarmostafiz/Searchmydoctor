from django.http import JsonResponse
from django.db import connection
from .models import Doctor

DEFAULT_SYNONYMS = {
    "heart": [
        "heart", "cardio", "cardiac", "cardiology", "cardiologist",
        "cardiothoracic", "heart surgery", "open heart surgery"
    ],
}

def expand_terms(q: str):
    base = (q or "").strip().lower()
    terms = set([base])
    terms.update(DEFAULT_SYNONYMS.get(base, []))
    return [t for t in terms if t]

def search_doctors(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)

    state = request.GET.get("state")
    city = request.GET.get("city")
    day = request.GET.get("day")  # 0..6
    at = request.GET.get("at")    # HH:MM or HH:MM:SS
    limit = int(request.GET.get("limit", "50"))

    terms = expand_terms(q)

    # Build boolean FULLTEXT query (OR terms)
    boolean_q = " ".join(terms)

    # FULLTEXT first: narrow down candidates using search_index
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT d.id
            FROM directory_doctor d
            JOIN directory_doctorsearchindex si ON si.doctor_id = d.id
            WHERE MATCH(si.search_text) AGAINST (%s IN BOOLEAN MODE)
            LIMIT %s
            """,
            [boolean_q, limit],
        )
        ids = [row[0] for row in cursor.fetchall()]

    qs = Doctor.objects.filter(id__in=ids).prefetch_related("specializations", "chambers__hospital")

    # Optional filters (state/city/day/time)
    if state:
        qs = qs.filter(chambers__state=state)
    if city:
        qs = qs.filter(chambers__city=city)

    if day is not None and day != "":
        qs = qs.filter(chambers__schedules__day_of_week=int(day))

    if at:
        # compare time within schedule
        qs = qs.filter(
            chambers__schedules__start_time__lte=at,
            chambers__schedules__end_time__gt=at,
        )

    qs = qs.distinct().order_by("full_name_ci")[:limit]

    data = []
    for d in qs:
        data.append({
            "id": d.id,
            "name": d.full_name,
            "photo": d.photo.url if d.photo else None,
            "specializations": [s.name for s in d.specializations.all()],
            "chambers": [
                {"name": c.name, "city": c.city, "state": c.state, "hospital": (c.hospital.name if c.hospital else None)}
                for c in d.chambers.all()
            ]
        })
    return JsonResponse(data, safe=False)



from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction

from .models import Doctor, Specialization, Chamber, ChamberSchedule


def doctor_list_ui(request):
    doctors = Doctor.objects.all().order_by("full_name_ci").prefetch_related("specializations", "chambers")
    return render(request, "ui/doctors/list.html", {"doctors": doctors})


@transaction.atomic
def doctor_create_ui(request):
    if request.method == "POST":
        # --- Doctor ---
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

        # --- Specializations (Select2 tags) ---
        # we submit specialization_names[] (strings)
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

        # --- Chambers (dynamic blocks) ---
        # we submit chamber_count and for each i: chamber_i_name, chamber_i_address, etc.
        chamber_count = int(request.POST.get("chamber_count") or 0)

        for i in range(chamber_count):
            prefix = f"chamber_{i}_"
            ch_name = (request.POST.get(prefix + "name") or "").strip()
            ch_address = (request.POST.get(prefix + "address") or "").strip()
            if not (ch_name and ch_address):
                # skip empty chamber blocks
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

            # schedules inside chamber: chamber_i_sched_count and rows: chamber_i_sched_j_day/start/end
            sched_count = int(request.POST.get(prefix + "sched_count") or 0)
            for j in range(sched_count):
                day = request.POST.get(prefix + f"sched_{j}_day")
                start = request.POST.get(prefix + f"sched_{j}_start")
                end = request.POST.get(prefix + f"sched_{j}_end")
                if not (day and start and end):
                    continue

                # day is int 0..6, start/end are "HH:MM"
                ChamberSchedule.objects.create(
                    chamber=chamber,
                    day_of_week=int(day),
                    start_time=start,
                    end_time=end,
                )

        messages.success(request, "Doctor created successfully")
        return redirect("doctor_list_ui")

    # GET
    # Provide existing specializations list for Select2 options
    specializations = Specialization.objects.all().order_by("name")
    return render(request, "ui/doctors/create.html", {"specializations": specializations})


def doctor_search_page(request):
    # IMPORTANT: do NOT pass doctors into template
    # Page loads with empty results.
    print("hello page")
    return render(request, "ui/search/search.html")

