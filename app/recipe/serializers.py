from rest_framework import serializers

from core.models import Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ["id", "title", "time_minutes", "price", "link", "tags"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])

        recipe = Recipe.objects.create(**validated_data)
        if tags:
            for tag in tags:
                auth_user = self.context["request"].user
                tag_obj, created = Tag.objects.get_or_create(
                    user=auth_user,
                    **tag,
                )
                recipe.tags.add(tag_obj)

        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        RecipeSerializer.Meta.fields += ["description"]

    # def create(self, validated_data):
    #     validated_data["user"] = self.context["user"]
    #     return super().create(validated_data)
