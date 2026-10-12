from django_filters import rest_framework as filters

from .models import Ticket


class TicketFilter(filters.FilterSet):
    # Explicit ChoiceFilters make an unknown value a 400 instead of silently returning nothing.
    status = filters.ChoiceFilter(choices=Ticket.Status.choices)
    priority = filters.ChoiceFilter(choices=Ticket.Priority.choices)

    class Meta:
        model = Ticket
        fields = ["status", "priority"]
