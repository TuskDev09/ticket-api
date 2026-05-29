from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User
from .models import Ticket


class AuthTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123',
            role=User.Role.USER
        )
        self.admin = User.objects.create_user(
            username='adminuser',
            email='admin@test.com',
            password='adminpass123',
            role=User.Role.ADMIN
        )

    def get_token(self, email, password):
        response = self.client.post(reverse('auth-login'), {
            'email': email,
            'password': password
        }, format='json')
        return response.data['access']

    def auth(self, email, password):
        token = self.get_token(email, password)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


class TicketPermissionTests(AuthTestCase):

    def setUp(self):
        super().setUp()
        self.auth('user@test.com', 'testpass123')
        self.ticket = Ticket.objects.create(
            title='Test ticket',
            description='Descripción de prueba',
            created_by=self.user
        )
        self.other_ticket = Ticket.objects.create(
            title='Ticket ajeno',
            description='No debería verlo',
            created_by=self.admin
        )

    def test_user_can_create_ticket(self):
        response = self.client.post(reverse('ticket-list'), {
            'title': 'Nuevo ticket',
            'description': 'Descripción',
            'priority': 'LOW',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_cannot_see_others_ticket(self):
        url = reverse('ticket-detail', args=[self.other_ticket.id])
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ])

    def test_user_cannot_delete_ticket(self):
        url = reverse('ticket-detail', args=[self.ticket.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_assign_ticket(self):
        url = reverse('ticket-detail', args=[self.ticket.id])
        response = self.client.patch(url, {
            'assigned_to_id': self.admin.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_status_transition(self):
        url = reverse('ticket-detail', args=[self.ticket.id])
        response = self.client.patch(url, {
            'status': 'CLOSED'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_status_transition(self):
        url = reverse('ticket-detail', args=[self.ticket.id])
        response = self.client.patch(url, {
            'status': 'IN_PROGRESS'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminTicketTests(AuthTestCase):

    def setUp(self):
        super().setUp()
        self.auth('admin@test.com', 'adminpass123')
        self.ticket = Ticket.objects.create(
            title='Ticket para admin',
            description='Descripción',
            created_by=self.user
        )

    def test_admin_can_delete_ticket(self):
        url = reverse('ticket-detail', args=[self.ticket.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_assign_ticket(self):
        url = reverse('ticket-detail', args=[self.ticket.id])
        response = self.client.patch(url, {
            'assigned_to_id': self.admin.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_see_all_tickets(self):
        response = self.client.get(reverse('ticket-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class AuthEndpointTests(AuthTestCase):

    def test_access_without_token_returns_401(self):
        response = self.client.get(reverse('ticket-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_returns_token(self):
        response = self.client.post(reverse('auth-login'), {
            'email': 'user@test.com',
            'password': 'testpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)