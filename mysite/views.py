from django.shortcuts import render, get_object_or_404, redirect
from read_statistics.utils import get_seven_days_read_data
from blog.models import Blog
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import datetime
from django.db.models import Sum,Q
from django.core.cache import cache
from django.core.paginator import Paginator


def get_7_days_hot_blogs():
    today = timezone.now().date()
    date = today - datetime.timedelta(7)
    blogs = Blog.objects.filter(read_details__date__lt=today, read_details__date__gte=date) \
        .values('id', 'title').annotate(read_num_sum=Sum('read_details__read_num')).order_by('-read_num_sum')
    return blogs[:5]


def get_today_hot_data():
    today = timezone.now().date()
    blogs = Blog.objects.filter(read_details__date=today) \
        .values('id', 'title').annotate(read_num_sum=Sum('read_details__read_num')) \
        .order_by('-read_num_sum')
    return blogs[:5]


def get_yesterday_hot_data():
    today = timezone.now().date()
    yesterday = today - datetime.timedelta(1)
    blogs = Blog.objects.filter(read_details__date=yesterday) \
        .values('id', 'title').annotate(read_num_sum=Sum('read_details__read_num')) \
        .order_by('-read_num_sum')
    return blogs[:5]


def home(request):
    blog_content_type = ContentType.objects.get_for_model(Blog)
    dates, read_nums = get_seven_days_read_data(blog_content_type)

    hot_blogs_for_7_days = cache.get('hot_blogs_for_7_days')
    today_hot_data = cache.get('today_hot_data')
    yesterday_hot_data = cache.get('yesterday_hot_data')
    if hot_blogs_for_7_days is None:
        hot_blogs_for_7_days = get_7_days_hot_blogs()
        cache.set('hot_blogs_for_7_days', hot_blogs_for_7_days, 3600)
    if today_hot_data is None:
        today_hot_data = get_today_hot_data()
        cache.set('today_hot_data', today_hot_data, 3600)
    if yesterday_hot_data is None:
        yesterday_hot_data = get_yesterday_hot_data()
        cache.set('yesterday_hot_data', yesterday_hot_data, 3600)

    context = {}
    context['read_nums'] = read_nums
    context['dates'] = dates
    context['today_hot_data'] = today_hot_data
    context['yesterday_hot_data'] = yesterday_hot_data
    context['hot_blogs_for_7_days'] = hot_blogs_for_7_days
    return render(request, 'home.html', context)


# def login(request):
#     # username=request.POST.get('username','')
#     # password=request.POST.get('password','')
#     # user=auth.authenticate(request,username=username,password=password)
#     # referer=request.META.get('HTTP_REFERER',reverse('home'))
#     # if user is not None:
#     #     auth.login(request,user)
#     #     return redirect(referer)
#     # else:
#     #     return render(request,'error.html',{'message':'用户名或密码不正确'})
#
#     if request.method == 'POST':
#         login_form = LoginForm(request.POST)
#         if login_form.is_valid():
#             user = login_form.cleaned_data['user']
#             auth.login(request, user)
#             return redirect(request.GET.get('from', reverse('home')))
#     else:
#         login_form = LoginForm()
#     context = {}
#     context['login_form'] = login_form
#     return render(request, 'login.html', context)
#
#
# def login_for_medal(request):
#     login_form = LoginForm(request.POST)
#     data = {}
#     if login_form.is_valid():
#         user = login_form.cleaned_data['user']
#         auth.login(request, user)
#         data['status'] = 'SUCCESS'
#     else:
#         data['status'] = 'ERROR'
#     return JsonResponse(data)
#
#
# def register(request):
#     if request.method == 'POST':
#         reg_form = RegForm(request.POST)
#         if reg_form.is_valid():
#             username = reg_form.cleaned_data['username']
#             email = reg_form.cleaned_data['email']
#             password = reg_form.cleaned_data['password']
#             user = User.objects.create_user(username, email, password)
#             user.save()
#             user = auth.authenticate(username=username, password=password)
#             auth.login(request, user)
#             return redirect(request.GET.get('from', reverse('home')))
#     else:
#         reg_form = RegForm()
#     context = {}
#     context['reg_form'] = reg_form
#     return render(request, 'register.html', context)
#
#
# def logout(request):
#     auth.logout(request)
#     return redirect(request.GET.get('from', reverse('home')))
#
#
# def user_info(request):
#     context = {}
#     return render(request, 'user_info.html', context)

def search(request):
    search_words=request.GET.get('wd','').strip()
    condition=None
    for word in search_words.split(' '):
        if condition is None:
            condition=Q(title__icontains=word)
        else:
            condition=condition | Q(title__icontains=word)
    search_blogs=[]
    if condition is not None:
        search_blogs=Blog.objects.filter(condition)

    page_num = request.GET.get('page', 1)
    paginator = Paginator(search_blogs,10)
    page_of_blogs = paginator.get_page(page_num)
    current_page_num = page_of_blogs.number
    # page_range=list(range(max(current_page_num-2,1),current_page_num))+list(range(current_page_num,min(current_page_num+2,paginator.num_pages)+1))
    page_range = [x for x in range(current_page_num - 2, current_page_num + 3) if 0 < x <= paginator.num_pages]
    if page_range[0] - 1 >= 2:
        page_range.insert(0, '...')
    if paginator.num_pages - page_range[-1] >= 2:
        page_range.append('...')
    if page_range[0] != 1:
        page_range.insert(0, 1)
    if page_range[-1] != paginator.num_pages:
        page_range.append(paginator.num_pages)

    context={}
    context['search_words']=search_words
    context['page_range'] = page_range
    context['page_of_blogs']=page_of_blogs
    context['search_blogs_count']=search_blogs.count()
    return render(request,'search.html',context)
