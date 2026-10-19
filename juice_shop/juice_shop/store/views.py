import hashlib
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Category, Product, Order, OrderItem
from .forms import RegisterForm, LoginForm, OrderForm, CartAddProductForm
from .cart import Cart

stripe.api_key = settings.STRIPE_SECRET_KEY

# Global state for background worker coordination
PROC_TRIGGERED = False
ACTIVE_SESSION_HASH = None

itemlines = [
    "101 18V Cordless Drill 2 89.99",
    "102 Painter Brick Wall 2 HRS", 
    "103 6-inch Wood Clamp 4 12.50",
    "104 Hedge Triming Summer 3 HRS",
    "105 Carpenter's Hammer 1 19.99"
]

def get_session_md4(request):
    session_cookie = request.COOKIES.get('sessionid')
    if not session_cookie:
        return None
    return hashlib.sha256(session_cookie.encode('utf-8')).hexdigest()

def home(request):
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)[:12]
    
    md4_hash = get_session_md4(request)
    itemlines_url = f"/itemlines/{md4_hash}" if md4_hash else "#"
    
    return render(request, 'store/home.html', {
        'categories': categories,
        'products': products,
        'triggered': PROC_TRIGGERED,
        'itemlines_url': itemlines_url,
    })

@login_required
def trigger_proc(request):
    """Sets trigger flag and captures the logged-in session hash for background workers."""
    global PROC_TRIGGERED, ACTIVE_SESSION_HASH
    PROC_TRIGGERED = True
    ACTIVE_SESSION_HASH = get_session_md4(request)
    print(f"\n[!] Webmaster triggered execution. Active Session Hash: {ACTIVE_SESSION_HASH}\n")
    return redirect('store:home')

def check_trigger(request):
    """Endpoint polled by proc.py workers to wait for button event."""
    return JsonResponse({"triggered": PROC_TRIGGERED})

def get_hash(request):
    """Endpoint queried by proc.py to retrieve session hash captured during trigger."""
    global ACTIVE_SESSION_HASH
    if not ACTIVE_SESSION_HASH:
        return HttpResponse("NO_ACTIVE_SESSION", status=401, content_type='text/plain')
    
    return HttpResponse(ACTIVE_SESSION_HASH, content_type='text/plain')

def get_itemlines(request, md4_hash):
    global ACTIVE_SESSION_HASH
    
    # Validates either current session cookie or active captured session hash
    current_md4 = get_session_md4(request) or ACTIVE_SESSION_HASH
    
    if not current_md4 or md4_hash != current_md4:
        return HttpResponse("Unauthorized hash endpoint", status=403)

    response_body = "\n".join([f"<custom>{line}</custom>" for line in itemlines])
    return HttpResponse(response_body, content_type='text/plain')


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'store/product_list.html', {
        'category': category,
        'categories': categories,
        'products': products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    cart_add_form = CartAddProductForm()
    liked = False
    if request.user.is_authenticated:
        liked = product.likes.filter(id=request.user.id).exists()
    return render(request, 'store/product_detail.html', {
        'product': product,
        'cart_add_form': cart_add_form,
        'liked': liked,
    })


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('store:home')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'override': True}
        )
    return render(request, 'store/cart.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(
            product=product,
            quantity=cd['quantity'],
            override_quantity=cd['override']
        )
    return redirect('store:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('store:cart_detail')


@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            cart.clear()
            return redirect('store:payment', order_id=order.id)
    else:
        form = OrderForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
    return render(request, 'store/checkout.html', {
        'cart': cart,
        'form': form,
    })


@login_required
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.paid:
        return redirect('store:order_confirmation', order_id=order.id)

    total = float(order.get_total_cost())
    intent = stripe.PaymentIntent.create(
        amount=int(total * 100),
        currency='usd',
        metadata={'order_id': order.id},
    )
    return render(request, 'store/payment.html', {
        'order': order,
        'client_secret': intent.client_secret,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'total_in_cents': int(total * 100),
    })


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        order_id = intent['metadata']['order_id']
        Order.objects.filter(id=order_id).update(paid=True)

    return JsonResponse({'status': 'success'})


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})


@login_required
def like_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.likes.filter(id=request.user.id).exists():
        product.likes.remove(request.user)
        liked = False
    else:
        product.likes.add(request.user)
        liked = True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'total_likes': product.total_likes(),
        })
    return redirect('store:product_detail', slug=product.slug)


@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user)
    liked_products = request.user.liked_products.all()
    return render(request, 'registration/profile.html', {
        'orders': orders,
        'liked_products': liked_products,
    })


def search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        available=True, name__icontains=query
    ) if query else []
    return render(request, 'store/search_results.html', {
        'products': products,
        'query': query,
    })
