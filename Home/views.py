from django.shortcuts import render
from django.contrib import messages

def home(request):
    return render(request, 'home/home.html')

def contact(request):
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        # For now, just show a success message
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return render(request, 'home/contact.html')
    
    return render(request, 'home/contact.html')
