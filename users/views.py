from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterFrom, ProfileUpdateForm, UserUpdateForm, ProfileCreateForm
from .models import Profile, Workgroup


def register(request):
    """Force Selection of Workgroup and update when created successfully"""
    if request.method == 'POST':
        u_form = UserRegisterFrom(request.POST)
        p_form = ProfileCreateForm(request.POST)
        if u_form.is_valid() and p_form.is_valid():
            username = u_form.cleaned_data.get('username')
            u_form.save()
            workgroup = Workgroup.objects.filter(name=p_form.cleaned_data.get('workgroup')).first()
            Profile.objects.filter(user__username=username).update(workgroup=workgroup)

            messages.success(request, f'Account for {username} successfully created. Please log in.')
            return redirect('login')
    else:
        u_form = UserRegisterFrom()
        p_form = ProfileCreateForm()

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'users/register.html', context)


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()

            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }

    return render(request, 'users/profile.html', context)
