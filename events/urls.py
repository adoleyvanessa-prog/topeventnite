from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('events/', views.event_list, name='event_list'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('create-event/', views.create_event, name='create_event'),
    path('book/<int:event_id>/', views.book_ticket, name='book_ticket'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path("booking-confirmation/<int:booking_id>/", views.booking_confirmation, 
         name="booking_confirmation"),
    path("events/<int:event_id>/attendees/", views.event_attendees, name="event_attendees"),
    path("payment/<int:booking_id>/", views.payment_page, name="payment_page"),
    path("payment/<int:booking_id>/complete/", views.complete_payment, name="complete_payment"),
]