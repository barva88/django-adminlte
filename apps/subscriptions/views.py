from django.shortcuts import render, redirect
from django.contrib import messages


def index(request):
    # blank page placeholder that still renders full AdminLTE layout
        # Reverted to a single sample plan to keep the page simple.
        plan = {
            'plan_id': 'pro',
            'plan_name': 'Pro',
            'price': '$29',
            'features': ['10 projects', 'Priority support', 'Team seats'],
            'badge': 'Popular',
        }
        return render(request, 'subscriptions/index.html', {'plan': plan})


def subscribe(request):
    if request.method == 'POST':
        # placeholder processing: in a real app you'd create subscription records,
        # charge a payment gateway, etc. Here we just simulate success.
        plan_id = request.POST.get('plan_id')
        messages.success(request, f'Subscription to "{plan_id}" processed successfully (simulated).')
        return redirect('subscriptions:index')
    return redirect('subscriptions:index')
