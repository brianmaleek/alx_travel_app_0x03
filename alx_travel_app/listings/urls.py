from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import ListingViewSet, BookingViewSet, PaymentInitiateView, PaymentVerifyView

router = DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet)

urlpatterns = [
    # ...other urls...
    path('payments/initiate/', PaymentInitiateView.as_view(), name='payment-initiate'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
]

urlpatterns += router.urls