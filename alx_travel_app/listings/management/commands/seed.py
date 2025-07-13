from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from listings.models import Listing, Booking, Review
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Seed the database with fake data for testing'

    def handle(self, *args, **kwargs):
        fake = Faker()
        users = []

        # Create 10 fake users
        for _ in range(10):
            user = User.objects.create_user(
                username=fake.user_name(),
                password='password',
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users.append(user)

        # Create 20 fake listings
        for _ in range(20):
            Listing.objects.create(
                title=fake.sentence(nb_words=6),
                host=random.choice(users),
                location=fake.city(),
                description=fake.text(max_nb_chars=200),
                price_per_night=random.uniform(50, 500),
                property_type=random.choice(Listing.PROPERTY_TYPES)[0],
                status=random.choice(Listing.STATUS_CHOICES)[0],
                max_guests=random.randint(1, 10),
                bedrooms=random.randint(1, 5),
                bathrooms=random.randint(1, 5)
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database with fake data'))

        # Create 30 fake bookings
        for _ in range(30):
            listing = random.choice(Listing.objects.all())
            guest = random.choice(users)
            check_in = fake.date_between(start_date='-1y', end_date='today')
            check_out = fake.date_between(start_date=check_in, end_date='+30d')
            guests_count = random.randint(1, listing.max_guests)
            total_price = listing.price_per_night * (check_out - check_in).days * guests_count

            Booking.objects.create(
                listing=listing,
                guest=guest,
                check_in=check_in,
                check_out=check_out,
                guests_count=guests_count,
                total_price=total_price,
                status=random.choice(Booking.STATUS_CHOICES)[0]
            )
        self.stdout.write(self.style.SUCCESS('Successfully created fake bookings'))

        # Create 50 fake reviews
        for _ in range(50):
            listing = random.choice(Listing.objects.all())
            reviewer = random.choice(users)
            rating = random.randint(1, 5)
            comment = fake.text(max_nb_chars=200)

            Review.objects.create(
                listing=listing,
                reviewer=reviewer,
                rating=rating,
                comment=comment
            )
        self.stdout.write(self.style.SUCCESS('Successfully created fake reviews'))
