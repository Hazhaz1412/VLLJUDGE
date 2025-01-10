"""
URL configuration for VLJudge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings 
from django.conf.urls.static import static
from django.urls import path
from home import views
from home.views import search_user, add_friend, activate
from home.views import get_home, get_problemsets, login_view, logout_view, get_contests, problem_detail, submit_code, user_submissions, submission_detail, register_view, all_submissions, profile_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', get_home, name='home'),  # Đặt tên cho URL của trang chủ
    path('problemsets/', get_problemsets),
    path('login/', login_view, name='login'),  # Đặt tên cho URL của trang đăng nhập
    path('logout/', logout_view),
    path('contests/', get_contests),
    path('problem/<int:problem_id>/', problem_detail, name='problem_detail'),
    path('submit_code/', submit_code, name='submit_code'),
    path('submissions/', user_submissions, name='user_submissions'),
    path('submission/<int:submission_id>/', submission_detail, name='submission_detail'),
    path('register/', register_view, name='register'),
    path('all_submissions/', all_submissions, name='all_submissions'),
    path('profile/', profile_view, name='profile'),
    path('search_user/', search_user, name='search_user'),
    path('add_friend/<int:user_id>/', add_friend, name='add_friend'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
