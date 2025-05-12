from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    user = get_user_model().objects.create_user(**params)
    return user


class PublicUserAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # self.client.force_authenticate(user=get_user_model()(is_staff=True))

    def test_if_user_registration_success_returns_201(self):
        payload = {
            "email": "test_user@gmail.com",
            "password": "test123456",
            "name": "reza",
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", response.data)

    def test_if_email_exists_when_user_register_returns_400(self):
        payload = {
            "email": "test2_user@gmail.com",
            "password": "test123456",
            "name": "reza",
        }

        create_user(**payload)
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_if_password_is_too_short_when_user_register_returns_400(self):
        payload = {
            "email": "test3_user@gmail.com",
            "password": "pw",
            "name": "reza",
        }

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload["email"]
        ).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user_returns_200(self):
        user_details = {
            "email": "test@gamil.com",
            "password": "password1",
            "name": "reza",
        }

        create_user(**user_details)

        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }
        response = self.client.post(TOKEN_URL, payload)
        self.assertIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_with_bad_credentials_returns_400(self):
        create_user(email="admin@gmail.com", password="password")
        payload = dict(email="other@gmail.com", password="123412341")
        response = self.client.post(TOKEN_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.data)

    def test_create_token_with_blank_password_returns_400(self):
        payload = dict(email="other@gmail.com", password="")
        response = self.client.post(TOKEN_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.data)

    def test_retrieve_unauthorized_user_returns_401(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITest(TestCase):
    def setUp(self):
        self.user = create_user(
            email="test@gmail.com",
            password="password1234",
            name="test",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_authorized_user_profile_returns_200(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "id": self.user.id,
            "email": self.user.email,
            "name": self.user.name,
        })

    def test_method_post_not_allowed_in_profile_and_returns_405(self):
        response = self.client.post(ME_URL, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_update_user_profile(self):
        payload = {
            "name": "new updated name",
            "password": "updated_pass",
        }
        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
