from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "office-home-2/",
        views.property_landing,
        {"property_slug": "office-home-2"},
        name="property_office_home_2",
    ),
    path(
        "office-home-3/",
        views.property_landing,
        {"property_slug": "office-home-3"},
        name="property_office_home_3",
    ),
    path(
        "office-home-2/bikes/<int:pk>/",
        views.bike_detail,
        {"property_slug": "office-home-2"},
        name="property_bike_detail_oh2",
    ),
    path(
        "office-home-3/bikes/<int:pk>/",
        views.bike_detail,
        {"property_slug": "office-home-3"},
        name="property_bike_detail_oh3",
    ),
    path("bikes/<int:pk>/", views.bike_detail, name="bike_detail"),
    path(
        "booking/<int:pk>/success/",
        views.booking_payment_success,
        name="booking_payment_success",
    ),
    path(
        "booking/<int:pk>/cancel/",
        views.booking_payment_cancel,
        name="booking_payment_cancel",
    ),
    path("routes/", views.routes_page, name="routes"),
]
