from django.conf.urls import include, url
from rest_framework.authtoken.views import obtain_auth_token
from board.urls import router

#urlpatterns = patterns('',
#    # Examples:
#    # url(r'^$', 'scrum.views.home', name='home'),
#    # url(r'^blog/', include('blog.urls')),
#
#    url(r'^api/token/', obtain_auth_token, name='api-token'),
#    url(r'^api/', include(router.urls)),
#    #url(r'^admin/', include(admin.site.urls)),
#)

urlpatterns = [
    url(r'^api/token/', obtain_auth_token, name='api-token'),
    url(r'^api/', include(router.urls)),

]
