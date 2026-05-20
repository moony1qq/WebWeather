from django.urls import path
from . import views

urlpatterns = [
    path("",                        views.index,            name="index"),
    path("current/",                views.current_weather,  name="current_weather"),
    path("forecast/",               views.forecast,         name="forecast"),
    path("history/",                views.history,          name="history"),
    path("register/",               views.register_view,    name="register"),
    path("login/",                  views.login_view,       name="login"),
    path("logout/",                 views.logout_view,      name="logout"),
    path("favorites/add/",          views.add_favorite,     name="add_favorite"),
    path("favorites/remove/<int:pk>/", views.remove_favorite, name="remove_favorite"),
]
