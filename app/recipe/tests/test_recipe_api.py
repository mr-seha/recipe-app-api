import tempfile
from decimal import Decimal
from pathlib import Path

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe, Tag
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_user(**params):
    return get_user_model().objects.create_user(**params)


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


class PublicRecipeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(RECIPES_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    def setUp(self):

        self.user = create_user(
            email="test_user@gmail.com",
            password="test123456",
            name="reza",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        create_recipe(self.user)
        create_recipe(self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, response.data)

    def test_recipes_list_limited_to_user(self):
        other_user = create_user(
            email="test2@gmail.com",
            password="test123456",
            name="ahmad",
        )

        create_recipe(self.user)
        create_recipe(other_user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_recipe_detail(self):
        recipe = create_recipe(user=self.user)

        response = self.client.get(detail_url(recipe.id))
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_recipe(self):
        payload = {
            "title": "test",
            "price": Decimal(10.5),
            "time_minutes": 5,
        }

        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data["id"])

        for key, value in payload.items():
            self.assertEqual(value, getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_recipe_partial_update(self):
        recipe = create_recipe(user=self.user)

        payload = {"title": "changed title"}

        response = self.client.patch(detail_url(recipe.id), payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.user, self.user)

    def test_recipe_full_update(self):
        recipe = create_recipe(user=self.user)
        payload = {
            "title": "recipe2",
            "description": "Another description",
            "price": Decimal(20.5),
            "time_minutes": 14,
            "link": "https://google.com",
        }

        response = self.client.put(detail_url(recipe.id), payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

    def test_update_user_returns_error(self):
        other_user = create_user(
            email="other_user@gmail.com",
            password="other4568",
            name="arash"
        )

        recipe = create_recipe(self.user)

        self.client.patch(detail_url(recipe.id), {"user": other_user})

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(self.user)
        recipe_url = detail_url(recipe.id)

        response = self.client.delete(recipe_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

        response = self.client.get(recipe_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_try_delete_another_users_recipe_returns_error(self):
        other_user = create_user(
            email="other_user@gmail.com",
            password="other4568",
            name="arash"
        )

        recipe = create_recipe(user=other_user)

        response = self.client.delete(detail_url(recipe.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        payload = {
            "title": "new recipe",
            "price": Decimal(10.45),
            "time_minutes": 10,
            "tags": [{"name": "tag1"}, {"name": "tag2"}]
        }

        response = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload["tags"]:
            exists = Tag.objects.filter(
                user=self.user,
                name=tag["name"]
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        tag_iranian = Tag.objects.create(user=self.user, name="iranian")
        payload = {
            "title": "other recipe",
            "price": Decimal(10.45),
            "time_minutes": 10,
            "tags": [{"name": "indian"}, {"name": "iranian"}]
        }

        response = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_iranian, recipe.tags.all())

        for tag in payload["tags"]:
            exists = Tag.objects.filter(
                user=self.user,
                name=tag["name"]
            ).exists()

            self.assertTrue(exists)

    def test_create_tag_on_recipe_update(self):
        recipe = create_recipe(user=self.user)
        tag_name = "tag1"
        payload = {"tags": [{"name": tag_name}]}

        response = self.client.patch(
            detail_url(recipe.id),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        filtered_tag = Tag.objects.filter(
            user=self.user,
            name=tag_name
        )
        recipe.refresh_from_db()
        self.assertTrue(filtered_tag.exists())
        self.assertEqual(recipe.tags.count(), 1)
        self.assertIn(filtered_tag.first(), recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        recipe = create_recipe(user=self.user)
        tag1 = Tag.objects.create(user=self.user, name="tag1")
        tag2 = Tag.objects.create(user=self.user, name="tag2")

        recipe.tags.add(tag1)

        payload = {"tags": [{"name": tag2.name}]}

        response = self.client.patch(
            detail_url(recipe.id),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        self.assertEqual(recipe.tags.count(), 1)
        self.assertNotIn(tag1, recipe.tags.all())
        self.assertIn(tag2, recipe.tags.all())

    def test_clear_recipe_tags(self):
        recipe = create_recipe(user=self.user)
        tag = Tag.objects.create(user=self.user, name="tag")
        recipe.tags.add(tag)

        payload = {"tags": []}
        response = self.client.patch(
            detail_url(recipe.id),
            payload,
            format="json",
        )
        recipe.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag, recipe.tags.all())
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        payload = {
            "title": "recipe",
            "price": Decimal(10.45),
            "time_minutes": 10,
            "ingredients": [{"name": "ing1"}]
        }
        response = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(pk=response.data["id"])
        self.assertEqual(recipe.ingredients.count(), 1)

        self.assertEqual(
            recipe.ingredients.all()[0].name,
            payload["ingredients"][0]["name"]
        )

    def test_create_recipe_with_existing_ingredients(self):
        ingredient_name = "ing1"
        created_ingredient = Ingredient.objects.create(
            user=self.user,
            name=ingredient_name
        )

        payload = {
            "title": "recipe",
            "price": Decimal(10.45),
            "time_minutes": 10,
            "ingredients": [{"name": ingredient_name}, {"name": "ing2"}]
        }

        response = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        queryset = Recipe.objects.filter(user=self.user)
        recipe = queryset[0]
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(created_ingredient, recipe.ingredients.all())

        for ingredient in payload["ingredients"]:
            self.assertTrue(
                recipe.ingredients.filter(
                    user=self.user,
                    name=ingredient["name"]
                ).exists()
            )

    def test_create_ingredients_on_update(self):

        recipe = create_recipe(user=self.user)

        payload = {
            "ingredients": [
                {"name": "ing1"},
                {"name": "ing new"}
            ]
        }

        response = self.client.patch(
            detail_url(recipe.id),
            payload,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload["ingredients"]:
            ingredient_obj = Ingredient.objects.get(
                user=self.user,
                name=ingredient["name"]
            )
            self.assertIn(ingredient_obj, recipe.ingredients.all())

    def test_update_recipe_assign_ingredients(self):
        ingredient1 = Ingredient.objects.create(user=self.user, name="ing1")

        ingredient2_name = "ing2"
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name=ingredient2_name
        )

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        payload = {"ingredients": [{"name": ingredient2_name}]}

        response = self.client.patch(
            detail_url(recipe.id),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_ingredients(self):
        ingredient = Ingredient.objects.create(user=self.user, name="ing1")

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {"ingredients": []}
        response = self.client.patch(
            detail_url(recipe.id),
            payload,
            format="json"
        )
        recipe.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_recipes_by_tags(self):
        recipe1 = create_recipe(user=self.user, title="recipe1")
        recipe2 = create_recipe(user=self.user, title="recipe2")

        tag1 = Tag.objects.create(user=self.user, name="tag1")
        tag2 = Tag.objects.create(user=self.user, name="tag2")
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        recipe3 = create_recipe(user=self.user, title="recipe3")

        params = {"tags": f"{tag1.id},{tag2.id}"}
        response = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(recipe1)
        s2 = RecipeSerializer(recipe2)
        s3 = RecipeSerializer(recipe3)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, response.data)
        self.assertIn(s2.data, response.data)
        self.assertNotIn(s3.data, response.data)

    def test_filter_recipes_by_ingredients(self):
        recipe1 = create_recipe(user=self.user, title="recipe1")
        recipe2 = create_recipe(user=self.user, title="recipe2")

        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name="ingredient1"
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name="ingredient2"
        )
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        recipe3 = create_recipe(user=self.user, title="recipe3")

        params = {"ingredients": f"{ingredient1.id},{ingredient2.id}"}
        response = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(recipe1)
        s2 = RecipeSerializer(recipe2)
        s3 = RecipeSerializer(recipe3)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, response.data)
        self.assertIn(s2.data, response.data)
        self.assertNotIn(s3.data, response.data)


class ImageUploadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@gmail.com",
            password="admin12345"
        )
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as img_file:
            img = Image.new('RGB', size=(10, 10))
            img.save(img_file, format="JPEG")
            img_file.seek(0)

            payload = {"image": img_file}
            response = self.client.post(url, payload, format="multipart")

            self.recipe.refresh_from_db()

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("image", response.data)
            self.assertTrue(Path(self.recipe.image.path).exists())

    def test_upload_image_bad_request(self):
        payload = {"image": "nonimage"}
        response = self.client.post(
            image_upload_url(self.recipe.id),
            payload,
            format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
