from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Ingredient, Recipe, Tag
from . import serializers


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="tags",
            description="Comma separated list of IDs to filter",
            type=str
        ),
        OpenApiParameter(
            name="ingredients",
            type=str,
            description="Comma separated list of IDs to filter",
        ),
    ],
)
class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        description="آپلود تصویر"
    )
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = serializers.RecipeImageSerializer(
            recipe,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def split_params_to_list(self, text):
        return [int(item) for item in text.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        tags = self.request.query_params.get("tags")
        ingredients = self.request.query_params.get("ingredients")

        if tags:
            tags = self.split_params_to_list(tags)
            queryset = queryset.filter(tags__id__in=tags)

        if ingredients:
            ingredients = self.split_params_to_list(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredients)

        return queryset.filter(user=user).order_by("-id").distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.RecipeSerializer
        elif self.action == "upload_image":
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BaseRecipeAttrViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        assigned_only = bool(self.request.query_params.get("assigned_only", 0))
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(user=user).order_by("-name").distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(BaseRecipeAttrViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
