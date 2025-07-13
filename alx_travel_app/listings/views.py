from django.shortcuts import render
from django.conf import settings
from rest_framework import viewsets
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer
from rest_framework.views import APIView
import os
import requests
from rest_framework.response import Response
from rest_framework import status
from .tasks import send_payment_confirmation_email, send_booking_confirmation_email

# Create your views here.
class ListingViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Listing instances.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Booking instances.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()

        # Send booking confirmation email
        send_booking_confirmation_email.delay(booking.id, booking.guest.email)

        # Automatically create a payment for the booking
        chapa_url = "https://api.chapa.co/v1/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {os.environ.get('CHAPA_SECRET_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "amount": booking.total_price,
            "currency": "ETB",
            "email": booking.guest.email,
            "first_name": booking.guest.first_name,
            "last_name": booking.guest.last_name,
            "tx_ref": f"booking_{booking.id}_{os.urandom(4).hex()}",
            "callback_url": f"{settings.SITE_URL}/api/payments/verify/"
        }
        chapa_response = requests.post(chapa_url, json=data, headers=headers)
        if chapa_response.status_code == 200:
            resp_data = chapa_response.json()
            transaction_id = resp_data['data']['tx_ref']
            Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                transaction_id=transaction_id,
                status='Pending'
            )
            booking.payment_checkout_url = resp_data['data']['checkout_url']
        else:
            # Handle the case where payment initiation fails
            Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                status='Failed',
            )

class PaymentInitiateView(APIView):
    """
    A view for initiating a payment.
    """
    def post(self, request, *args, **kwargs):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            chapa_url = "https://api.chapa.co/v1/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {os.environ.get('CHAPA_SECRET_KEY')}",
                "Content-Type": "application/json"
            }
            data = {
                "amount": serializer.validated_data['amount'],
                "currency": "ETB",
                "email": request.data.get('email'),
                "first_name": request.data.get('first_name', ''),
                "last_name": request.data.get('last_name', ''),
                "tx_ref": f"booking_{serializer.validated_data['booking'].id}_{os.urandom(4).hex()}",
                "callback_url": request.build_absolute_uri('/api/payments/verify/')
            }
            chapa_response = requests.post(chapa_url, json=data, headers=headers)
            if chapa_response.status_code == 200:
                resp_data = chapa_response.json()
                transaction_id = resp_data['data']['tx_ref']
                payment = serializer.save(transaction_id=transaction_id, status='Pending')
                return Response({
                    "payment": PaymentSerializer(payment).data,
                    "checkout_url": resp_data['data']['checkout_url']
                }, status=status.HTTP_201_CREATED)
            return Response({"error": "Failed to initiate payment"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentVerifyView(APIView):
    """
    A view for verifying a payment.
    """
    def get(self, request, *args, **kwargs):
        tx_ref = request.query_params.get('tx_ref')
        if not tx_ref:
            return Response({"error": "tx_ref is required"}, status=status.HTTP_400_BAD_REQUEST)
        chapa_url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
        headers = {
            "Authorization": f"Bearer {os.environ.get('CHAPA_SECRET_KEY')}",
        }
        chapa_response = requests.get(chapa_url, headers=headers)
        if chapa_response.status_code == 200:
            resp_data = chapa_response.json()
            try:
                payment = Payment.objects.get(transaction_id=tx_ref)
                if resp_data['data']['status'] == 'success':
                    payment.status = 'Completed'
                    payment.save()
                    send_payment_confirmation_email.delay(payment.booking.id, payment.booking.guest.email)
                else:
                    payment.status = 'Failed'
                    payment.save()
                return Response({"status": payment.status})
            except Payment.DoesNotExist:
                return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "Failed to verify payment"}, status=status.HTTP_400_BAD_REQUEST)
