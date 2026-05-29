from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet
from comments.views import CommentListCreateView

router = DefaultRouter()
router.register('', TicketViewSet, basename='ticket')

urlpatterns = [
    path('<int:ticket_id>/comments', CommentListCreateView.as_view(), name='ticket-comments'),
    path('', include(router.urls)),
]
