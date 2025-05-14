from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


def tag_detail_url(tag_id):
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="test@gmail.com", password="12345test"):
    user = get_user_model().objects.create_user(
        email=email,
        password=password,
    )

    return user


def create_tag(user, name="test"):
    return Tag.objects.create(user=user, name=name)


class PublicTagsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITest(TestCase):
    def setUp(self):
        self.user = create_user()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        create_tag(self.user)
        create_tag(self.user, name="other tag")

        tags = Tag.objects.all().order_by("-name")

        response = self.client.get(TAGS_URL)
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        other_user = create_user(email="other@gmail.com", password="test555")
        tag = create_tag(self.user)
        create_tag(other_user)

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], tag.id)
        self.assertEqual(response.data[0]["name"], tag.name)
        self.assertEqual(len(response.data), 1)

    def test_update_tag(self):
        tag = create_tag(self.user, name="my tag")

        payload = {"name": "new name"}
        response = self.client.patch(tag_detail_url(tag.id), payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])
