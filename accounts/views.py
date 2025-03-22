from django.shortcuts import render, redirect
# from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout



User = get_user_model()  # Lấy model User đang sử dụng

def signup(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirmpassword = request.POST.get('confirmpassword')
        
        # Kiểm tra mật khẩu khớp nhau
        if password != confirmpassword:
            messages.error(request, "Passwords do not match!")
            return redirect('accounts:signup')
        
        # Kiểm tra username hoặc email đã tồn tại chưa
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken!")
            return redirect('accounts:signup')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered!")
            return redirect('accounts:signup')
        
        # Tạo user mới
        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=firstname,
            last_name=lastname
        )
        
        messages.success(request, "Account created successfully.")
        return redirect('accounts:signin')
    if request.user.is_authenticated:
        return redirect('userLogin:dashboard')
    return render(request, 'accounts/signup.html')



def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = None
        try:
            user = User.objects.get(username=username)
        except :
            messages.error(request, "Invalid username or password.")
        
        if user is not None:
            print(username)
            if user.is_active:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, "Login successful.")
                    return redirect('userLogin:dashboard')
                messages.error(request, "Invalid username or password.")
                return redirect('accounts:signin')
                
            else:
                messages.error(request, "Your account has been banned or deactivated.")
        return redirect('accounts:signin')
    if request.user.is_authenticated:
        return redirect('userLogin:dashboard')
    return render(request, 'accounts/signin.html')



def signout(request):
    logout(request)
    messages.success(request, 'Logout successful.')
    return redirect('news:home')