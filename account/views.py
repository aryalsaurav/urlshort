from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User,AnonymousUser 
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from .models import UrlShortener
import string
import random
import io
import qrcode

from datetime import datetime
from django.utils.timezone import make_aware

# Create your views here.


def login_view(request):
    if request.method == "GET":
        return render(request, "login.html")
    
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect("/short/url/")
        else:
            return render(request, "login.html")


@login_required(login_url="/login/")
def logout_view(request):
    user = request.user
    logout(request)
    return HttpResponseRedirect("/login/")



@login_required(login_url="/login/")
def index(request):
    urls = UrlShortener.objects.filter().order_by("-id")
    return render(request, 'index.html', {'urls': urls})


def generate_short_url():
    characters = string.digits + string.ascii_letters
    short_url = "".join(random.choice(characters) for i in range(6))
    return short_url



# def creat_short_url(request):
    
#     original_url = request.GET.get("url")
#     key = request.GET.get("key")
#     time = request.GET.get("time")

#     if time:
#         time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
#     else:
#         time = None
#     if key:
#         find_key = UrlShortener.objects.filter(short_url=key)
#         if find_key:
#             return HttpResponse("Key already exist")
#         else:
#             short_url = key
#     else:
#         short_url = generate_short_url()
#     short_url_inst = UrlShortener.objects.create(long_url=original_url, short_url=short_url, expiration_time=time)
#     short_url_inst.save()
#     return HttpResponse(short_url)

@login_required
def create_short_url(request):
    user = request.user
    now  = timezone.now()
    if request.method == 'POST':
        original_url = request.POST.get('original_url')
        custom_alias = request.POST.get('custom_alias') or None
        exp_str = request.POST.get('expiration_time')
        expiration_time = None

        # Validate URL
        if not original_url:
            return redirect('account:home')

        # Parse expiration_time
        if exp_str:
            try:
                # from datetime-local: YYYY-MM-DDTHH:MM
                dt = datetime.strptime(exp_str, '%Y-%m-%dT%H:%M')
                expiration_time = timezone.make_aware(dt, timezone.get_current_timezone())
            except ValueError:
                return redirect('account:home')

        # 1) Reuse existing non-expired entry?
        existing = (
            UrlShortener.objects
            .filter(long_url=original_url, user=user)
            .filter(Q(expiration_time__gt=now) | Q(expiration_time__isnull=True))
            .first()
        )
        if existing:
            # Extend expiration if new time is later
            if expiration_time and (
               not existing.expiration_time or expiration_time > existing.expiration_time
            ):
                existing.expiration_time = expiration_time
                existing.save(update_fields=['expiration_time'])
            else:
                messages.error(request, "Short url with this token already exists.")
                return redirect('account:home')

        # 2) Determine unique short_code
        if custom_alias:
            conflict = (
                UrlShortener.objects
                .filter(short_url=custom_alias, user=user)
                .filter(Q(expiration_time__gt=now) | Q(expiration_time__isnull=True))
                .exists()
            )
            if conflict:
                return redirect('account:home')
            short_code = custom_alias
        else:
            short_code = generate_short_url()
            # avoid collisions
            while (
                UrlShortener.objects
                .filter(short_url=short_code, user=user)
                .filter(Q(expiration_time__gt=now) | Q(expiration_time__isnull=True))
                .exists()
            ):
                short_code = generate_short_url()

        # 3) Create the record
        obj = UrlShortener.objects.create(
            user=user,
            long_url=original_url,
            short_url=short_code,
            expiration_time=expiration_time,
        )

        # 4) Generate & attach QR code
        full_url = request.build_absolute_uri(f'/{obj.short_url}')
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(full_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        qr_filename = f"{short_code}.png"
        obj.qr_code.save(qr_filename, ContentFile(buffer.read()), save=False)
        obj.save()

        return redirect('account:home')
    

@login_required(login_url="/login/")
def shorten_url(request):
    return render(request, "shorten_url.html")

@login_required(login_url="/login/")
def short_url_detail(request, short_url):
    
    short_url_obj = get_object_or_404(UrlShortener, short_url=short_url)
    window_domain = request.get_host()
    short_url_is = f"http://{window_domain}/{short_url_obj.short_url}"
    return render(request, "short_url_detail.html", {"object": short_url_obj, "short_url": short_url_is})


def short_url_list(request):
    short_url_list = UrlShortener.objects.all()
    return render(request, "short_url_list.html", {"object_list": short_url_list})



def short_url_redirect(request, short_url):

    short_url_obj = get_object_or_404(UrlShortener, short_url=short_url)
    if short_url_obj.expiration_time:
        expiration_time = short_url_obj.expiration_time
        if expiration_time < make_aware(datetime.now()):
            return HttpResponse("This short url has expired")
    short_url_obj.count += 1
    short_url_obj.save()
    return HttpResponseRedirect(f'{short_url_obj.long_url}')
    