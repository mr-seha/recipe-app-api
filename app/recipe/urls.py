from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, TagViewSet

app_name = "recipe"

router = DefaultRouter()

router.register("recipes", RecipeViewSet)
router.register("tags", TagViewSet)
urlpatterns = router.urls
