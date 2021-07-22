from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, SimpleTestCase, TransactionTestCase, LiveServerTestCase
from django.urls import reverse, resolve

from project.apps.bidinterpreter.views import *
from django.contrib.auth import get_user_model
from django.conf import settings

from mixer.backend.django import mixer
from parameterized import parameterized

settings.DEBUG = True

class Routes(SimpleTestCase):
    allow_database_queries = True
    @classmethod
    def setUpClass(self):
        super(Routes, self).setUpClass()
        # print("all users", get_user_model().objects.all())
        self.user = get_user_model().objects.get(username="dave")

    @classmethod
    def tearDownClass(self):
        """ Prevent database from being destroyed. """
        pass

    def test_poo(self):
        pass

    def inactive_test_resolution_for_foo(self):
        resolver = resolve('/bidinterpreter/3/')
        self.assertEqual(resolver.func.cls, DetailView)

    def test_url_detail_view(self):
        """ Insures bid summary / deal landing page works for id 1 """
        url = reverse('bidinterpreter:detail', args=[3])
        self.assertEqual(url, '/bidinterpreter/3/')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        # print('response...', dir(response), response.content)

    def test_url_auth_detail_view_successful(self):
        """ This test ensures that users are properly redirected """

        login_successful = self.client.force_login(self.user)


        # self.request.user = AnonymousUser()
        url = reverse('bidinterpreter:detail', kwargs={'pk': 3})
        # print("url is:", url, self.user.is_active)
        self.assertEqual(url, '/bidinterpreter/3/')
        response = self.client.get(url, follow=True)
        # print("response is:", response)
        self.assertTrue(response.context['user'].is_active)
 
    @parameterized.expand([
       ("bidinterpreter_detail_authorized",         "bidinterpreter:detail",    "with_user",    {'pk': 3}, "/bidinterpreter/3/"),
       ("bidinterpreter_detail_unauthorized",       "bidinterpreter:detail",    "unauthorized", {'pk': 3}, "/bidinterpreter/3/"),
       ("bidinterpreter_deal_add_authorized",       "bidinterpreter:deal-add",  "with_user",    {},        "/bidinterpreter/deal/add/"),
       ("bidinterpreter_deal_add_unauthorized",     "bidinterpreter:deal-add",  "unauthorized", {},        "/bidinterpreter/deal/add/"),
       ("bidinterpreter_deal_update_authorized",    "bidinterpreter:bid-update","with_user",    {'pk': 1}, "/bidinterpreter/bid/1/update/"),
       ("bidinterpreter_deal_update_unauthorized",  "bidinterpreter:bid-update","unauthorized", {'pk': 1}, "/bidinterpreter/bid/1/update/"),
       ("bidinterpreter_add_bid_authorized",        "bidinterpreter:bid-add",   "with_user",    {'pk': 3}, "/bidinterpreter/deal/3/add_bid/"),
       ("bidinterpreter_add_bid_unauthorized",      "bidinterpreter:bid-add",   "unauthorized", {'pk': 3}, "/bidinterpreter/deal/3/add_bid/"),
       ("bidinterpreter_update_bid_authorized",     "bidinterpreter:bid-update","with_user",    {'pk': 1}, "/bidinterpreter/bid/1/update/"),
       ("bidinterpreter_update_bid_unauthorized",   "bidinterpreter:bid-update","unauthorized", {'pk': 1}, "/bidinterpreter/bid/1/update/"),
       ("bidinterpreter_search_authorized",         "bidinterpreter:search",    "with_user",    {},        "/bidinterpreter/search/"),
       ("bidinterpreter_search_unauthorized",       "bidinterpreter:search",    "unauthorized", {},        "/bidinterpreter/search/"),
       ("bidinterpreter_search_json_authorized",    "bidinterpreter:search-json","with_user",   {},        "/bidinterpreter/search/json/"),
       ("bidinterpreter_search_json_unauthorized",  "bidinterpreter:search-json","unauthorized",{},        "/bidinterpreter/search/json/"),
       ## /bidinterpreter/deal/3/add_bid/
       # ("integer", 1, 1.0),
       # ("large fraction", 1.6, 1),
    ])
    def test_url_route(self, test_name, route_name, user_login, reverse_kwargs, resolved_url):

        if user_login == "with_user":
            login_successful = self.client.force_login(self.user)

        # self.request.user = AnonymousUser()
        url = reverse(route_name, kwargs=reverse_kwargs)
        # print("url is:", url, self.user.is_active)
        self.assertEqual(url, resolved_url)
        response = self.client.get(url, follow=True)
        # print("user is active", response.context['user'].is_active)
        # print("response is:", response)
        if user_login == "with_user":
            self.assertTrue(response.context['user'].is_active)
        else:
            test = False if not response.context['user'].is_active else True
            self.assertFalse(test)

        # Test that anonymouse users can't access page

        