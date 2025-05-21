from rest_framework import serializers

from core.models import Ingredient, Recipe, Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "time_minutes",
            "price",
            "link",
            "tags",
            "ingredients"
        ]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, recipe: Recipe, tags):
        user = self.context["request"].user

        if tags:
            for tag in tags:
                tag_obj, created = Tag.objects.get_or_create(
                    user=user,
                    **tag,
                )
                recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, recipe: Recipe, ingredients):
        user = self.context["request"].user
        if ingredients:
            for ingredient in ingredients:
                ingredient_obj, created = Ingredient.objects.get_or_create(
                    user=user,
                    **ingredient,
                )
                recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])

        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_tags(recipe, tags)
        self._get_or_create_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance: Recipe, validated_data):
        tags = validated_data.pop("tags", None)
        instance.tags.clear()
        self._get_or_create_tags(instance, tags)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        RecipeSerializer.Meta.fields += ["description"]

    # def create(self, validated_data):
    #     validated_data["user"] = self.context["user"]
    #     return super().create(validated_data)
