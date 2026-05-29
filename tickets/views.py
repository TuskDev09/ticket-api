from rest_framework import viewsets, permissions, filters
from rest_framework.pagination import PageNumberPagination

from .models import Ticket
from .serializers import TicketSerializer
from .permissions import TicketPermission


class TicketPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = (TicketPermission,)
    pagination_class = TicketPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('created_at', 'updated_at', 'priority', 'status')
    ordering = ('-created_at',)

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.select_related('created_by', 'assigned_to').all()

        if user.role != 'ADMIN':
            queryset = queryset.filter(created_by=user)

        status = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        assigned_to = self.request.query_params.get('assigned_to')

        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)