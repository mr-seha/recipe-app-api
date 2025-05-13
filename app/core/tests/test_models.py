from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from core.models import Recipe, Tag


def create_user(email="test@gmail.com", password="1234abcd1234"):
    user = get_user_model().objects.create_user(
        email=email,
        password=password,
    )
    return user


class ModelTests(TestCase):
    def test_create_user(self):
        email = "test@gmail.com"
        password = "1234abcd1234"

        user = create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_normalize_email(self):
        sample_emails = [
            ["test1@Gmail.com", "test1@gmail.com"],
            ["test2@gmail.COM", "test2@gmail.com"],
            ["test3@GMAIL.com", "test3@gmail.com"],
        ]
        for email, expected in sample_emails:
            user = create_user(
                email=email,
                password="password1"
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise_error(self):
        with self.assertRaises(ValueError):
            create_user(email="", password="1234test")

    def test_create_superuser(self):
        email = "test@gmail.com"
        password = "test1234"
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = create_user(
            email="test@gmail.com",
            password="test_pass1",
        )

        recipe = Recipe.objects.create(
            user=user,
            title="new recipe",
            description="sample recipe description ...",
            price=Decimal("15.45"),
            time_minutes=5,
        )

        self.assertEqual(recipe.title, str(recipe))

    def test_create_tag(self):
        user = create_user()
        tag = Tag.objects.create(user=user, name="new tag")

        self.assertEqual(str(tag), tag.name)
