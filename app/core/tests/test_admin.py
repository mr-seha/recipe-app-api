from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status


class AdminSiteTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin2@gmail.com",
            password="admin_user",
        )
        self.client = Client()
        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email="normaluser@gmail.com",
            password="normal_user",
        )

    def test_users_list(self):
        url = reverse("admin:core_user_changelist")
        response = self.client.get(url)
        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)

    def test_edit_user_page(self):
        url = reverse("admin:core_user_change", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # @unittest.skip
    def test_create_user_page(self):
        url = reverse("admin:core_user_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
