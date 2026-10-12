from rest_framework.routers import SimpleRouter

from .views import TicketViewSet

router = SimpleRouter(trailing_slash=False)
router.register("tickets", TicketViewSet, basename="ticket")

urlpatterns = router.urls
