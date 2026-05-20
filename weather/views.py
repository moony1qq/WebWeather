from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .services import WeatherService
from .models import SearchHistory, FavoriteCity
from .forms import RegisterForm

service = WeatherService()


# ─── Auth ───────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect("index")
    else:
        form = RegisterForm()
    return render(request, "weather/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    error = None
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("index")
        else:
            error = "Invalid username or password."
    return render(request, "weather/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")


# ─── Main ────────────────────────────────────────────

@login_required
def index(request):
    history = SearchHistory.objects.filter(user=request.user)[:8]
    favorites = FavoriteCity.objects.filter(user=request.user)
    return render(request, "weather/index.html", {
        "history": history,
        "favorites": favorites,
    })


@login_required
def current_weather(request):
    if request.method == "POST":
        city = request.POST.get("city", "").strip()
        if not city:
            messages.error(request, "Please enter a city name.")
            return redirect("index")
        try:
            weather = service.get_current_weather(city)
            SearchHistory.objects.create(
                user=request.user,
                city=weather.city,
                country=weather.country,
                search_type="current",
                temperature=weather.temperature,
                description=weather.description,
            )
            is_favorite = FavoriteCity.objects.filter(
                user=request.user, city=weather.city
            ).exists()
            return render(request, "weather/current.html", {
                "weather": weather,
                "is_favorite": is_favorite,
            })
        except ValueError as e:
            messages.error(request, str(e))
        except ConnectionError:
            messages.error(request, "Network error. Please try again.")
    return redirect("index")


@login_required
def forecast(request):
    if request.method == "POST":
        city = request.POST.get("city", "").strip()
        if not city:
            messages.error(request, "Please enter a city name.")
            return redirect("index")
        try:
            forecast_data = service.get_forecast(city)
            SearchHistory.objects.create(
                user=request.user,
                city=forecast_data.city,
                country=forecast_data.country,
                search_type="forecast",
                description=f"{len(forecast_data.days)}-day forecast",
            )
            return render(request, "weather/forecast.html", {
                "forecast": forecast_data,
            })
        except ValueError as e:
            messages.error(request, str(e))
        except ConnectionError:
            messages.error(request, "Network error. Please try again.")
    return redirect("index")


@login_required
def history(request):
    all_history = SearchHistory.objects.filter(user=request.user)
    return render(request, "weather/history.html", {"history": all_history})


# ─── Favorites ───────────────────────────────────────

@login_required
def add_favorite(request):
    if request.method == "POST":
        city = request.POST.get("city", "").strip()
        country = request.POST.get("country", "").strip()
        if city:
            FavoriteCity.objects.get_or_create(
                user=request.user, city=city,
                defaults={"country": country}
            )
            messages.success(request, f"{city} added to favorites!")
    return redirect(request.POST.get("next", "index"))


@login_required
def remove_favorite(request, pk):
    fav = get_object_or_404(FavoriteCity, pk=pk, user=request.user)
    fav.delete()
    messages.info(request, f"{fav.city} removed from favorites.")
    return redirect("index")
