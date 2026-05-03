from django.urls import path

from doctor_search.directory.views_ui import admin_dashboard
from .api import bd_division_detail_api, bd_divisions_api, get_districts_by_division, get_location_by_district
from .views import search_doctors
from .views_ui import doctor_edit_ui, doctor_search_page, doctor_list_ui, doctor_create_ui, admin_dashboard

urlpatterns = [
    # Landing page = Search UI
    path("", doctor_search_page, name="home"),

    # JSON API
    path("search/doctors", search_doctors, name="search_doctors"),

    # Superuser-only Admin UI
    path("app/admin", admin_dashboard, name="admin_dashboard"),
    path("app/admin/doctors", doctor_list_ui, name="doctor_list_ui"),
    path("app/admin/doctors/create", doctor_create_ui, name="doctor_create_ui"),
    path("app/admin/doctors/<int:doctor_id>/edit", doctor_edit_ui, name="doctor_edit_ui"),
    path("api/bd/divisions/", bd_divisions_api, name="bd_divisions_api"),
    path("api/bd/division/<str:division_id>/", get_districts_by_division, name="bd_division_detail_api"),
    path("api/bd/district/<str:district_id>/", get_location_by_district, name="bd_division_detail_api"),
]
    # path("search/doctors", search_doctors, name="search_doctors"),
    # path("ui/doctors", doctor_list_ui, name="doctor_list_ui"),
    # path("ui/doctors/create", doctor_create_ui, name="doctor_create_ui"),
    # path("ui/search", doctor_search_page, name="doctor_search_page"),

    # # JSON API
    # path("search/doctors", search_doctors, name="search_doctors"),
    #  path("app/admin", admin_dashboard, name="admin_dashboard"),
    # path("app/admin/doctors", doctor_list_ui, name="doctor_list_ui"),
    # path("app/admin/doctors/create", doctor_create_ui, name="doctor_create_ui"),
    # ]
