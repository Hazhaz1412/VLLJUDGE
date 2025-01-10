from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import subprocess
import os
import time
from django.http import JsonResponse
import tempfile
from .forms import RegisterForm
from django.conf import settings 
from .models import Problem
from .models import Submission
import re
from django.contrib.auth.decorators import login_required
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from datetime import datetime
from django.db.models import Q   
from .models import Profile 
from .forms import ProfileForm
from django.contrib.auth.models import User
from .forms import UserSearchForm
from .models import FriendRequest
from .models import RatingChange
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.utils.timezone import timedelta
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from .forms import RegisterForm, LoginForm
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.template.loader import render_to_string 
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Đăng nhập thành công nếu tài khoản đã được xác thực
                    login(request, user)
                    return redirect('/')
                else:
                    if form.cleaned_data.get('resend_activation_email'):
                        # Nếu người dùng yêu cầu gửi lại email xác thực
                        send_activation_email(user, request)
                        form.add_error(None, 'Your account is not active. A new activation email has been sent to you.')
                    else:
                        form.add_error(None, 'Your account is not active. Please check your email for the activation link.')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def send_activation_email(user, request):
    current_site = get_current_site(request)
    mail_subject = 'Activate your account'
    
    # Tải nội dung HTML từ template
    html_message = render_to_string('activation_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    
    # Loại bỏ thẻ HTML để làm nội dung văn bản thuần (tùy chọn)
    plain_message = strip_tags(html_message)
    
    # Gửi email
    send_mail(
        subject=mail_subject,
        message=plain_message,  # Nội dung thuần văn bản
        from_email='noreply@vljudge.com',
        recipient_list=[user.email],
        html_message=html_message,  # Nội dung HTML
    )

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')
    else:
        return render(request, 'activation_invalid.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_activation_email(user, request)
            return render(request, 'registration_pending.html')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})



@login_required
def search_user(request):
    if request.method == 'GET':
        form = UserSearchForm(request.GET)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(username=username)
                profile, created = Profile.objects.get_or_create(user=user)
                
                if not profile.avatar:
                    profile.avatar_url = settings.MEDIA_URL + 'default.jpg'
                else:
                    profile.avatar_url = profile.avatar.url
                # Truyền form đúng vào context
                total_solve = len(user.accepted_problems)
                submissions = Submission.objects.filter(user=user).order_by('submitted_at')
                chart_data = {
                    'labels': [submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S') for submission in submissions],
                    'points': [profile.points for _ in submissions],
                }
                context = {
                    'searched_user': user,
                    'profile': profile,
                    'total_solve': total_solve,
                    'chart_data': chart_data,
                }
                
                return render(request, 'searched_profile.html', context)
            except User.DoesNotExist:
                form.add_error('username', 'User does not exist')
    else:
        form = UserSearchForm()

    return render(request, 'profile.html', {'form': form})  # Render đúng form UserSearchForm


@login_required
def profile_view(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    solved_problems = user.accepted_problems  # Ensure this is a list or queryset
    solved_problems_count = len(solved_problems)

    # Provide a default avatar URL if the user has not uploaded an avatar
    if not profile.avatar:
        profile.avatar_url = settings.MEDIA_URL + 'default.jpg'
    else:
        profile.avatar_url = profile.avatar.url

    # Determine rank title and color based on points
    if profile.points < 800:
        profile.rank_title = "Newbie"
        profile.rank_color = "gray"
    elif profile.points < 1200:
        profile.rank_title = "Pupil"
        profile.rank_color = "green"
    elif profile.points < 1600:
        profile.rank_title = "Specialist"
        profile.rank_color = "blue"
    elif profile.points < 2000:
        profile.rank_title = "Expert"
        profile.rank_color = "purple"
    elif profile.points < 2200:
        profile.rank_title = "Candidate Master"
        profile.rank_color = "Orange"
    elif profile.points < 2400:
        profile.rank_title = "Master"
        profile.rank_color = "DarkOrange"

    # Save the rating change for today if it doesn't already exist
    today = timezone.now().date()
    if not RatingChange.objects.filter(user=user, date=today).exists():
        RatingChange.objects.create(user=user, rating=profile.points)

    # Prepare data for the chart
    rating_changes = RatingChange.objects.filter(user=user).order_by('date')
    chart_data = {
        'labels': [change.date.strftime('%Y-%m-%d') for change in rating_changes],
        'points': [change.rating for change in rating_changes],
    }

    # Handle user search
    if 'username' in request.GET:
        search_form = UserSearchForm(request.GET)
        if search_form.is_valid():
            username = search_form.cleaned_data['username']
            return redirect('searched_profile', username=username)
    else:
        search_form = UserSearchForm()

    context = {
        'user': user,
        'profile': profile,
        'solved_problems': solved_problems,
        'solved_problems_count': solved_problems_count,
        'form': form,
        'chart_data': chart_data,
        'search_form': search_form,
    }
    return render(request, 'profile.html', context)

@login_required
def add_friend(request, user_id):
    try:
        user_to_add = User.objects.get(id=user_id)
        # Check if a friend request already exists
        if not FriendRequest.objects.filter(from_user=request.user, to_user=user_to_add).exists():
            FriendRequest.objects.create(from_user=request.user, to_user=user_to_add)
        return redirect('profile')
    except User.DoesNotExist:
        return redirect('search_user')
    
 
def get_home(request):
    return render(request, 'home.html')

 

def get_different_line(expected_output, user_output):
    expected_lines = expected_output.split('\n')
    user_lines = user_output.split('\n')
    for idx, (exp_line, user_line) in enumerate(zip(expected_lines, user_lines)):
        if exp_line != user_line:
            return idx + 1, exp_line, user_line
    return -1, "", ""  # Nếu không tìm thấy dòng khác nhau

@login_required
def user_submissions(request):
    submissions_list = Submission.objects.filter(user=request.user).order_by('-submitted_at')
    paginator = Paginator(submissions_list, 25)  # 25 submissions per page

    page_number = request.GET.get('page')
    submissions = paginator.get_page(page_number)
    return render(request, 'submissions.html', {'submissions': submissions})
def all_submissions(request):
    submissions_list = Submission.objects.all().order_by('-submitted_at')
    paginator = Paginator(submissions_list, 25)  # 25 submissions per page

    page_number = request.GET.get('page')
    submissions = paginator.get_page(page_number)
    return render(request, 'all_submissions.html', {'submissions': submissions})
@login_required
def submission_detail(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    problem_id = submission.problem.id
    testcases = []

    # Load hidden testcases
    hidden_testcases = load_hidden_testcases(problem_id)
     
    testcase_result_pattern = re.compile(
        r'Testcase (\d+): (Passed|Failed)(?: - ([^\n]+))?', re.DOTALL)
    testcase_output_pattern = re.compile(
        r'Testcase (\d+):\s*(.*?)(?=(?:Testcase \d+:|$))', re.DOTALL)
 
    results = {int(m.group(1)): {
        'status': m.group(2),
        'details': m.group(3) if m.group(3) else ''
    } for m in testcase_result_pattern.finditer(submission.result)}
 
    outputs = {int(m.group(1)): m.group(2).strip() for m in testcase_output_pattern.finditer(submission.outputs)}
 
    for i, (input_data, expected_output) in enumerate(hidden_testcases, start=1):
        result = results.get(i)
        actual_output = outputs.get(i, '')

        if result:
            if result['status'] == "Passed":
                testcases.append({
                    'status': 'Passed',
                    'input': input_data,
                    'expected': expected_output,
                    'actual': actual_output,
                    'comment': 'Ok, passed'
                })
            else:
                line_number, expected_line, user_line = get_different_line(expected_output, actual_output)
                testcases.append({
                    'status': 'Failed',
                    'input': input_data,
                    'expected': expected_output,
                    'actual': actual_output,
                    'comment': f'Wrong Answer at line {line_number}: Expected: {expected_line}\nGot: {user_line}'
                })
        else:
            testcases.append({
                'status': 'Missing',
                'input': input_data,
                'expected': expected_output,
                'actual': actual_output,
                'comment': 'Testcase result missing or not processed'
            })
 
    return JsonResponse({
        'source_code': submission.source_code,
        'problem_title': submission.problem_title,
        'language': submission.language,
        'status': submission.status,
        'time_limit': submission.time_limit,
        'memory_used': submission.memory_used,
        'submitted_at': submission.submitted_at,
        'testcases': testcases
    })
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Problem, Submission
from django.db.models import Q


def get_problemsets(request):
    problems = Problem.objects.all()
    tag = request.GET.get('tag')
    rating_min = request.GET.get('rating_min')
    rating_max = request.GET.get('rating_max')

    if tag:
        problems = problems.filter(tags__icontains=tag)
    if rating_min:
        problems = problems.filter(rating__gte=rating_min)
    if rating_max:
        problems = problems.filter(rating__lte=rating_max)

    # Pagination
    paginator = Paginator(problems, 25)  # 25 bài toán mỗi trang
    page_number = request.GET.get('page')
    problems_page = paginator.get_page(page_number)

    # Lấy tất cả các tags
    tags = Problem.objects.values_list('tags', flat=True).distinct()

    problem_status = {}
    if request.user.is_authenticated:
        # Lấy thông tin về trạng thái của các bài toán mà người dùng đã giải
        accepted_problems = [int(id) for id in request.user.accepted_problems]
        tried_problems = [int(id) for id in request.user.tried_problems]
        for problem in problems_page:
            if problem.id in accepted_problems:
                problem_status[problem.id] = 'solved'
            elif problem.id in tried_problems:
                problem_status[problem.id] = 'tried'
            else:
                problem_status[problem.id] = 'not_tried'
    else:
        for problem in problems_page:
            problem_status[problem.id] = 'not_tried'

    return render(request, 'problemsets.html', {
        'problems': problems_page,
        'tags': tags,
        'problem_status': problem_status
    })
 

def logout_view(request):
    logout(request)
    return redirect('/')

def get_contests(request):
    return render(request, 'contests.html')

def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    sample_testcases = problem.sample_testcases.split('Testcase')
    sample_testcases = [tc.strip() for tc in sample_testcases if tc.strip()]
    parsed_testcases = []
    
    for testcase in sample_testcases:
        input_start = testcase.find('Input:') + len('Input:')
        output_start = testcase.find('Output:')
        input_data = testcase[input_start:output_start].strip()
        output_data = testcase[output_start + len('Output:'):].strip()
        parsed_testcases.append({'input': input_data, 'output': output_data})
    return render(request, 'problem_detail.html', {'problem': problem, 'sample_testcases': parsed_testcases})
        
def notify_submission_update(submission):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "submissions",
        {
            "type": "submission_update",
            "submission": {
                "id": submission.id,
                "problem_title": submission.problem_title,
                "language": submission.language,
                "status": submission.status,
                "time_limit": submission.time_limit,
                "memory_used": submission.memory_used,
                "submitted_at": submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                "author": submission.user.username,  # Thêm tên người dùng
            },
        },
    )
def load_hidden_testcases(problem_id):
    """
    Load multiple hidden test cases from a file based on the problem ID.
    """
    file_path = os.path.join(settings.MEDIA_ROOT, 'hidden_testcases', f'hidden_testcases_{problem_id}.txt')
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Hidden test case file for problem ID {problem_id} not found.")

    with open(file_path, 'r') as file:
        data = file.read().strip()

    testcases = []
    blocks = data.split('Testcase ')
    for block in blocks[1:]:
        parts = block.split('Output:')
        if len(parts) < 2:
            continue
        input_part = parts[0].split('Input:')[1].strip() if 'Input:' in parts[0] else ''
        output_part = parts[1].strip()
        testcases.append((input_part, output_part))

    return testcases
 
 
@login_required
@csrf_exempt
def submit_code(request):
    if request.method == 'POST':
        problem_id = request.POST.get('problem_id')
        language = request.POST.get('language')
        code = request.POST.get('code')
        problem = Problem.objects.get(id=problem_id)
        time_limit = problem.time_limit
        memory_limit = problem.memory_limit

        with tempfile.NamedTemporaryFile(delete=False, suffix='.py' if language == 'python' else '.cpp') as temp_code_file:
            temp_code_file.write(code.encode('utf-8'))
            temp_code_file_path = temp_code_file.name

        try:
            docker_command = [
                'docker', 'run', '--rm',
                '-v', f'{temp_code_file_path}:/app/code.{language}',
                '-v', os.path.join(settings.MEDIA_ROOT, 'hidden_testcases') + ':/app/hidden_testcases:ro',
                'vljudge',
                'python3', '/app/judge.py', language,
                f'/app/code.{language}',
                str(problem_id),
                str(time_limit),
                str(memory_limit)
            ]

            print(f"Running command: {' '.join(docker_command)}")

            result = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=60
            )

            print(f"Result from Docker: {result.stdout}")
            output = result.stdout

        except subprocess.TimeoutExpired:
            output = "Judging process timed out."
        except FileNotFoundError:
            output = "File not found error."
        except Exception as e:
            output = f"Error: {str(e)}"

        os.remove(temp_code_file_path)

        time_used = 0
        memory_used = 0
        testcase_pattern = re.compile(r'Testcase \d+: Passed - Time: ([\d.]+)ms, Memory: ([\d.]+)KB')
        for match in testcase_pattern.finditer(output):
            time = float(match.group(1)) / 1000
            memory = float(match.group(2))
            if time > time_used:
                time_used = time
            if memory > memory_used:
                memory_used = memory

        final_status_pattern = re.compile(r'Final status: (.+)')
        final_status_match = final_status_pattern.search(output)
        final_status = final_status_match.group(1) if final_status_match else "Compiler Error"

        user_outputs_pattern = re.compile(r'User Outputs:\n((?:.|\n)+)')
        user_outputs_match = user_outputs_pattern.search(output)
        user_outputs = user_outputs_match.group(1).strip() if user_outputs_match else ""
        submit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            problem_title=problem.title,
            source_code=code,
            language=language,
            status=final_status,
            result=output,
            outputs=user_outputs,
            submitted_at=submit_time,
            memory_used=memory_used,
            time_limit=time_used
        )

        # Update user's accepted and tried problems
        if final_status == 'Accepted':
            if problem_id in request.user.tried_problems:
                request.user.tried_problems.remove(problem_id)
            if problem_id not in request.user.accepted_problems:
                request.user.accepted_problems.append(problem_id)
                # Increase the solved count for the problem
                problem.solved_count += 1
                problem.save()
        else:
            if problem_id not in request.user.tried_problems and problem_id not in request.user.accepted_problems:
                request.user.tried_problems.append(problem_id)

        request.user.save()

        notify_submission_update(submission)

        return redirect('user_submissions')

    return JsonResponse({'error': 'Invalid request method'}, status=400)