from django.core.management.base import BaseCommand, CommandError
from project.apps.bidinterpreter.models import Deal, Bid
from django.contrib.auth.models import User

from faker import Faker
from faker.providers import company
import random

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        # parser.add_argument('n_deals', nargs='+', type=int)
        # parser.add_argument('n_bids',  nargs='+', type=int)
        parser.add_argument('-u', '--users', type=int, help="# of users to create.", default = 0)
        parser.add_argument('-d', '--deals', type=int, help="# of deals to create.", default = 0)
        parser.add_argument('-b', '--bids',  type=int, help="# of bids to create.", default = 100)

    def handle(self, *args, **options):
        fake = Faker()
        fake.add_provider(company)

        if options['users']:
            for index in range(options['users']):
                try:
                    first, last = fake.name().split()
                    user = User.objects.create_user(f"{first.lower()}_{last.lower()}", "test@localhost", "test")
                    user.username   = f"{first_name}_{last_name}"
                    user.first_name = first
                    user.last_name  = last
                    user.save()

                    self.stdout.write(self.style.SUCCESS('Successfully created user "%s"' % fake.name()))

                except Exception as e:
                    print("Couldn't create user", e)

        if options['deals']:

            suffixes = ['Villas', 'Apts', 'Apartments', 'Courtyard', 'Village', 'Housing Complex', 'Battle Dome Apts', 'Shanty Town', 'Condos', 'Townhomes', 'West', 'South', 'Homes', 'Building Complex', 'No-Mold Apts', 'Luxury Alley Homes']
            for deal_index in range(options['deals']):
                random_user = User.objects.order_by('?').first()
                deal_name = f"{fake.company()} {random.choice(suffixes)}"
                deal = Deal.objects.create(deal_name = deal_name)
                
                self.stdout.write(self.style.SUCCESS('Successfully created deal "%s"' % deal_name))

                # add bids

                for bid_index in range(options['bids']):
                    try:
                        random_user = User.objects.order_by('?').first()
                        bid = Bid.objects.create(
                            deal            = deal,
                            user            = random_user,
                            purchase_price  = 12345678,
                            due_diligence   = "21 days",
                            closing         = "Randomness TBD for this field",
                            comments        = "this is a randomly generated bid",
                            deposit         = "12345678",
                            status          = 3
                        )
                    except Exception as e:
                        print("Couldn't create bid", e)

                # try:
                #     poll = Poll.objects.get(pk=poll_id)
                # except Poll.DoesNotExist:
                #     raise CommandError('Poll "%s" does not exist' % poll_id)

                # poll.opened = False
                # poll.save()

            