from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def create_user(email="test@gmail.com", password="test1234567"):
    return get_user_model().objects.create_user(email=email, password=password)


def create_ingredient(user, name="ing"):
    return Ingredient.objects.create(user=user, name=name)


class PublicIngredientsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_is_anonymous(self):
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITest(TestCase):
    def setUp(self):
        self.user = create_user()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient(self):
        create_ingredient(user=self.user)

        response = self.client.get(INGREDIENTS_URL)

        queryset = Ingredient.objects.order_by("-name")
        serializer = IngredientSerializer(queryset, many=True)

        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ingredient_limited_to_user(self):
        other_user = create_user(email="other@gmail.com", password="test1234")
        create_ingredient(user=other_user, name="ing1")
        ingredient2 = create_ingredient(user=self.user, name="ing2")

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], ingredient2.name)
        self.assertEqual(response.data[0]["id"], ingredient2.id)
