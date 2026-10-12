from django.db import connection
from django.db.models import Count
from django.http import JsonResponse
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import TicketFilter
from .models import Ticket
from .serializers import TicketSerializer, TicketUpdateSerializer


def health(request):
    """Liveness/readiness probe: also verifies the database is reachable."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


class TicketViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """POST /tickets, GET /tickets, PATCH /tickets/<id>, GET /tickets/stats."""

    queryset = Ticket.objects.all()
    filterset_class = TicketFilter
    lookup_value_regex = "[0-9]+"
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        return TicketUpdateSerializer if self.action == "partial_update" else TicketSerializer

    def partial_update(self, request, *args, **kwargs):
        ticket = self.get_object()
        serializer = self.get_serializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TicketSerializer(ticket).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Ticket counts grouped by status; statuses with no tickets are reported as 0."""
        counts = dict(Ticket.objects.order_by().values_list("status").annotate(n=Count("id")))
        return Response({status: counts.get(status, 0) for status in Ticket.Status.values})
