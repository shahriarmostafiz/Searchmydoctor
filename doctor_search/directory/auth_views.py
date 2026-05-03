from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def superuser_login_view(request):
    
    if request.user.is_authenticated:
        # If already logged in, only allow superuser into admin UI
        if request.user.is_superuser:
            return redirect("admin_dashboard")
        logout(request)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Invalid credentials.")
            return redirect("login")

        if not user.is_superuser:
            messages.error(request, "Only superusers can access this admin panel.")
            return redirect("login")

        login(request, user)
        return redirect("admin_dashboard")

    return render(request, "ui/auth/login.html")

def superuser_logout_view(request):
    logout(request)
    return redirect("home")
