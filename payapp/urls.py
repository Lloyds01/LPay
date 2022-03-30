
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pay/',include('pay.urls')),
    path('main/',include('main.urls'))
]
