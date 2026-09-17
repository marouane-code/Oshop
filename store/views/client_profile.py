from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import UserProfile, Order

@login_required
def profile_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user, defaults={
        'full_name': user.get_full_name() or user.username,
        'phone': '',
        'address': '',
        'city': 'Casablanca'
    })
    
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', '')
        profile.phone = request.POST.get('phone', '')
        profile.address = request.POST.get('address', '')
        profile.city = request.POST.get('city', '')
        profile.save()
        
        user.first_name = profile.full_name
        user.save()
        
        messages.success(request, "Your profile information has been updated successfully.")
        return redirect('store:profile')
        
    orders = Order.objects.filter(user=user).prefetch_related('items').order_by('-created_at')
    
    context = {
        'profile': profile,
        'orders': orders,
    }
    return render(request, 'client/profile.html', context)
