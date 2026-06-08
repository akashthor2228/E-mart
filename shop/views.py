from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

from .form import CustomUserCreationForm
from .models import *
import json
import razorpay
import hmac
import hashlib
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required


# ── Home ───────────────────────────────────────────────────
def home(request):
    products = Product.objects.filter(trending=1)
    return render(request, 'index.html', {'products': products})


# ── Cart ───────────────────────────────────────────────────
def cart_page(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user)
        return render(request, 'cart.html', {'cart': cart})
    else:
        return redirect('/')


# ── Auth ───────────────────────────────────────────────────
def login_page(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == "POST":
        name = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=name, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You are now logged in')
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('/login')
    return render(request, 'login.html')


def register_page(request):
    form = CustomUserCreationForm()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully')
            return redirect('/login')
    return render(request, 'register.html', {'form': form})


def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You are now logged out')
    return redirect('/')


# ── Collections ────────────────────────────────────────────
def product_page(request):
    category = Category.objects.filter(status=0)
    return render(request, 'collections.html', {"category": category})


def colectionsview(request, name):
    if Category.objects.filter(name=name, status=0).exists():
        products = Product.objects.filter(category__name=name)
        return render(request, 'products/index.html', {"products": products, "category_name": name})
    else:
        messages.warning(request, 'Category not found')
        return redirect('collections')


def product_details(request, cname, pname):
    if Category.objects.filter(name=cname, status=0).exists():
        product = Product.objects.filter(name=pname, status=0).first()
        if product:
            return render(request, 'products/product_details.html', {"products": product})
        else:
            messages.warning(request, 'Product not found')
            return redirect('collections')
    else:
        messages.warning(request, 'Category not found')
        return redirect('collections')


# ── Cart Actions ───────────────────────────────────────────
def add_to_cart(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            data = json.loads(request.body)
            product_qty = int(data['product_qty'])
            product_id = data['pid']
            try:
                product_status = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'status': 'Product Not Found'}, status=200)

            if Cart.objects.filter(user=request.user, product_id=product_id).exists():
                return JsonResponse({'status': 'Product Already In Cart'}, status=200)
            elif product_status.quantity >= product_qty:
                Cart.objects.create(user=request.user, product_id=product_id, product_qty=product_qty)
                return JsonResponse({'status': 'Product Added to Cart'}, status=200)
            else:
                return JsonResponse({'status': 'Product Stock Not Available'}, status=200)
        else:
            return JsonResponse({'status': 'Login to Add Cart'}, status=200)
    return JsonResponse({'status': 'Invalid Access'}, status=200)


def remove_cart(request, cid):
    Cart.objects.filter(id=cid).delete()
    return redirect('/cart')


# ── Favourites ─────────────────────────────────────────────
def fav_page(request):
    if request.user.is_authenticated:
        fav = Fav.objects.filter(user=request.user)
        return render(request, 'fav.html', {'fav': fav})
    else:
        return redirect('/')


def add_to_fav(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            data = json.loads(request.body)
            pid = data.get('pid')
            try:
                product = Product.objects.get(id=pid)
            except Product.DoesNotExist:
                return JsonResponse({'status': 'Product Not Found'}, status=200)
            fav_item, created = Fav.objects.get_or_create(user=request.user, product=product)
            if created:
                return JsonResponse({'status': 'Added to Favourites!'}, status=200)
            else:
                return JsonResponse({'status': 'Already in Favourites!'}, status=200)
        else:
            return JsonResponse({'status': 'Login to Add Favourite'}, status=200)
    return JsonResponse({'status': 'Invalid Access'}, status=200)


def remove_fav(request, cid):
    Fav.objects.filter(id=cid).delete()
    return redirect('/fav')


# ── Checkout ───────────────────────────────────────────────
def checkout(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user)
        if not cart.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('/cart')
        total = sum(item.total_cost for item in cart)
        razorpay_key = settings.RAZORPAY_KEY_ID
        return render(request, 'checkout.html', {
            'cart': cart,
            'total': total,
            'razorpay_key': razorpay_key,
        })
    else:
        return redirect('/login')


# ── Create Razorpay Order ──────────────────────────────────
@login_required
def create_order(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'Invalid Method'}, status=405)

    cart = Cart.objects.filter(user=request.user)
    if not cart.exists():
        return JsonResponse({'status': 'Cart is empty'}, status=400)

    total_paise = int(sum(item.total_cost for item in cart) * 100)

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        rz_order = client.order.create({
            "amount": total_paise,
            "currency": "INR",
            "payment_capture": 1
        })
    except Exception as e:
        return JsonResponse({'status': 'Razorpay error', 'message': str(e)}, status=500)

    Order.objects.create(
        user=request.user,
        razorpay_order_id=rz_order["id"],
        amount=total_paise / 100
    )

    return JsonResponse({
        "order_id": rz_order["id"],
        "amount": total_paise,
        "currency": "INR",
        "key": settings.RAZORPAY_KEY_ID,
        "name": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        # Prefill UPI / contact info for the Razorpay modal
        "contact": "",   # optionally pull from user profile
    })


# ── Verify Payment ─────────────────────────────────────────
# NOTE: @csrf_exempt is required because Razorpay posts back without a Django
# CSRF token. We manually authenticate the request using HMAC-SHA256 instead.
@csrf_exempt
def verify_payment(request):
    if request.method != "POST":
        return JsonResponse({'status': 'Invalid Method'}, status=405)

    try:
        data = json.loads(request.body)

        razorpay_order_id   = data["razorpay_order_id"]
        razorpay_payment_id = data["razorpay_payment_id"]
        razorpay_signature  = data["razorpay_signature"]

        # ── HMAC-SHA256 signature verification ────────────────
        msg = f"{razorpay_order_id}|{razorpay_payment_id}"
        gen_sig = hmac.new(              # hmac.new IS correct in Python std-lib
            settings.RAZORPAY_KEY_SECRET.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()

        if gen_sig != razorpay_signature:
            return JsonResponse({"status": "failed", "message": "Signature mismatch"}, status=400)

        # ── Mark order paid ───────────────────────────────────
        updated = Order.objects.filter(razorpay_order_id=razorpay_order_id).update(
            razorpay_payment_id=razorpay_payment_id,
            status="paid"
        )
        if not updated:
            return JsonResponse({"status": "error", "message": "Order not found"}, status=404)

        # ── Clear cart for the order owner ────────────────────
        # request.user may be AnonymousUser here because @csrf_exempt bypasses
        # session middleware in some setups — look up the user via the order instead.
        order = Order.objects.get(razorpay_order_id=razorpay_order_id)
        Cart.objects.filter(user=order.user).delete()

        return JsonResponse({"status": "success"})

    except KeyError as e:
        return JsonResponse({"status": "error", "message": f"Missing field: {e}"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# ── Order Success ──────────────────────────────────────────
def order_success(request):
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, status="paid").last()
        return render(request, 'order_success.html', {'order': order})
    else:
        return redirect('/')