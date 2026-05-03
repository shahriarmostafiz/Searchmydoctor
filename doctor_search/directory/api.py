
import requests

from doctor_search.directory.models import AllDistricts, AllDivisions
from .data import GEO_DATA, DIVISIONS
from django.http import JsonResponse

def bd_divisions_api(request):
    try:
        divisions = AllDivisions.objects.all().values("id", "name", "name_bn")

        return JsonResponse(
            {"data": list(divisions)},
            safe=False,
            status=200
        )
        
    except requests.RequestException as e:
        return JsonResponse({
            "status": {"code": 500, "message": "failed"},
            "error": str(e)
        }, status=500)



from django.http import JsonResponse
from django.db import connection
from collections import defaultdict
import json

def get_districts_by_division1(request,division ):
    # division = request.GET.get('division')

    if not division:
        return JsonResponse({"error": "Division is required"}, status=400)

    query = """
        SELECT 
            district,
            postcode,
            JSON_ARRAYAGG(DISTINCT thana) AS areas
        FROM districts
        WHERE division = %s
        GROUP BY district, postcode
        ORDER BY district, postcode;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [division])
        rows = cursor.fetchall()

    # district -> list of postcode groups
    grouped = defaultdict(list)

    for district, postcode, areas in rows:
        grouped[district].append({
            "postcode": postcode,
            "areas": json.loads(areas) if isinstance(areas, str) else areas
        })

    response = []

    for district, upazilla in grouped.items():
        response.append({
            "district": district,
            "districtbn": "",
            "coordinates": "",
            "upazilla": upazilla
        })

    return JsonResponse({"data": response})




def get_districts_by_division2(request, division):
    if not division:
        return JsonResponse({"error": "Division is required"}, status=400)

    query = """
            SELECT 
                district,
                postcode,
                JSON_ARRAYAGG(thana) AS areas
            FROM (
                SELECT 
                    district,
                    thana,
                    MIN(postcode) AS postcode
                FROM districts
                WHERE LOWER(division) = LOWER(%s)
                GROUP BY district, thana
            ) t
            GROUP BY district, postcode
            ORDER BY district, postcode;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [division])
        rows = cursor.fetchall()

    # district -> list of postcode groups
    grouped = defaultdict(list)

    for district, postcode, areas in rows:
        # handle JSON safely
        areas_list = json.loads(areas) if isinstance(areas, str) else areas

        grouped[district].append({
            "postcode": postcode,
            "areas": sorted(areas_list, key=lambda x: x.lower())  # already distinct from subquery
        })

    response = []

    for district, upazilla in grouped.items():
        response.append({
            "district": district,
            "districtbn": "",
            "coordinates": "",
            "upazilla": upazilla
        })

    return JsonResponse({"data": response}, safe=False)

from collections import defaultdict
from django.http import JsonResponse

def get_districts_by_division(request, division):
    if not division:
        return JsonResponse({"error": "Division is required"}, status=400)

    query = """
        SELECT district, thana
        FROM districts
        WHERE LOWER(division) = LOWER(%s)
        GROUP BY district, thana
        ORDER BY district, thana;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [division])
        rows = cursor.fetchall()

    grouped = defaultdict(list)

    for district, thana in rows:
        grouped[district].append(thana)

    response = []

    for district, thanas in grouped.items():
        response.append({
            "district": district,
            "upazilla": sorted(thanas, key=lambda x: x.lower())
        })

    return JsonResponse({"data": response})
def get_location_by_district(request, district_id):
    if not district_id:
        return JsonResponse({"error": "District id is required"}, status=400)

    try:
        district = AllDistricts.objects.get(id=district_id)
    except AllDistricts.DoesNotExist:
        return JsonResponse({"error": "District not found"}, status=404)

    # Get upazilas
    upazilas = list(
        district.allupazilas_set.all().values("id", "name", "name_bn")
    )

    # Get thanas
    thanas = list(
        district.allthanas_set.all().values("id", "name", "name_bn")
    )

    # Merge both into one list
    combined = upazilas + thanas

    return JsonResponse({
        "district": {
            "id": district.id,
            "name": district.name,
            "name_bn": district.name_bn,
        },
        "upazilas": combined
    })

def get_districts_by_division(request, division_id):
    if not division_id:
        return JsonResponse({"error": "Division id is required"}, status=400)

    try:
        division = AllDivisions.objects.get(id=division_id)
    except AllDivisions.DoesNotExist:
        return JsonResponse({"error": "Division not found"}, status=404)

    districts = division.alldistricts_set.all().values(
        "id", "name", "name_bn"
    )

    return JsonResponse(
        {
            "division": {
                "id": division.id,
                "name": division.name,
                "name_bn": division.name_bn,
            },
            "data": list(districts)
        },
        safe=False,
        status=200
    )



def bd_division_detail_api(request, division):
    try:
        division = (division or "").strip().lower()
        res = GEO_DATA.get(division)
        # requests.get(f"https://bdapis.com/api/v1.2/division/{division}", timeout=15)
        return JsonResponse(res, safe=False, status=200)
    except requests.RequestException as e:
        return JsonResponse({
            "status": {"code": 500, "message": "failed"},
            "error": str(e)
        }, status=500)