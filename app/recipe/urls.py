from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet

app_name = "recipe"

router = DefaultRouter()

router.register("recipes", RecipeViewSet)
router.register("tags", TagViewSet)

router.register("ingredients", IngredientViewSet)
urlpatterns = router.urls
