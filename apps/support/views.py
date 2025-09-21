from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import SupportTopic, SupportTicket
from .forms import SupportTicketForm
from rest_framework import viewsets, permissions
from .serializers import SupportTopicSerializer, SupportTicketSerializer


class SupportIndexView(View):
    def get(self, request):
        topics = SupportTopic.objects.filter(is_active=True).order_by('ordering')
        return render(request, 'support/support_index.html', {'topics': topics})


class SupportNewView(View):
    def get(self, request):
        form = SupportTicketForm(user=request.user)
        return render(request, 'support/support_new.html', {'form': form})

    def post(self, request):
        form = SupportTicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user
            ticket.save()
            return redirect('support:my_tickets')
        return render(request, 'support/support_new.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class SupportMyTicketsView(View):
    def get(self, request):
        tickets = SupportTicket.objects.filter(user=request.user)
        return render(request, 'support/support_my_tickets.html', {'tickets': tickets})


class SupportTicketDetailView(View):
    def get(self, request, id):
        ticket = get_object_or_404(SupportTicket, pk=id)
        # permission: owner or staff
        if ticket.user and ticket.user != request.user and not request.user.is_staff:
            return redirect('support:index')
        return render(request, 'support/support_detail.html', {'ticket': ticket})


# DRF
class SupportTopicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SupportTopic.objects.filter(is_active=True).order_by('ordering')
    serializer_class = SupportTopicSerializer
    permission_classes = [permissions.AllowAny]


class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.IsAuthenticated()] if not self.request.user.is_staff else [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SupportTicket.objects.all()
        if user.is_authenticated:
            return SupportTicket.objects.filter(user=user)
        return SupportTicket.objects.none()

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)
