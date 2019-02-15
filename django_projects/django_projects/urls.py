from django.conf.urls import patterns, include, url
from django.contrib import admin
from registration.forms import RegistrationFormUniqueEmail
from registration.backends.default.views import RegistrationView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'django_projects.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^erdiagram/', include('django_spaghetti.urls')),
    url(r'^frank/', include('frank.urls')),
    url(r'^register/$',
       RegistrationView.as_view(),
       name='registration_register'),
    url(r'^accounts/register/$',
       RegistrationView.as_view(),
       name='registration_register'),
    url(r'^accounts/', include('registration.backends.default.urls')),

)