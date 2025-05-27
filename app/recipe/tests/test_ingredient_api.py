from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def get_detail(ingredient_id):
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="test@gmail.com", password="test1234567"):
    return get_user_model().objects.create_user(email=email, password=password)


def create_ingredient(user, name="ing"):
    return Ingredient.objects.create(user=user, name=name)


def create_recipe(user, **params):
    defaults = {
        "title": "new recipe",
        "description": "sample recipe description",
        "price": Decimal(10.45),
        "time_minutes": 10,
        "link": "https://yahoo.com",
    }

    defaults.update(user=user, **params)
    return Recipe.objects.create(**defaults)


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

    def test_update_ingredient(self):
        ingredient = create_ingredient(user=self.user)

        payload = {"name": "new ing"}
        response = self.client.patch(get_detail(ingredient.id), payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        ingredient = create_ingredient(user=self.user)

        response = self.client.delete(get_detail(ingredient.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredients_assigned_to_recipies(self):
        ingredient1 = create_ingredient(user=self.user, name="ing1")
        ingredient2 = create_ingredient(user=self.user, name="ing2")

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        params = {"assigned_only": 1}
        response = self.client.get(INGREDIENTS_URL, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        s1 = IngredientSerializer(ingredient1)
        s2 = IngredientSerializer(ingredient2)

        self.assertIn(s1.data, response.data)
        self.assertNotIn(s2.data, response.data)

    def test_filtered_ingredients_unique(self):
        ingredient = create_ingredient(user=self.user, name="ing")
        create_ingredient(user=self.user, name="other")

        recipe1 = create_recipe(user=self.user, title="recipe1")
        recipe2 = create_recipe(user=self.user, title="recipe2")

        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        params = {"assigned_only": 1}
        response = self.client.get(INGREDIENTS_URL, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
