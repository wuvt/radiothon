from settings import *

DEBUG=True
TEMPLATE_DEBUG=DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'radiothon',
        'USER': 'root',
        'PASSWORD': 'toor',
        'HOST': '',
        'PORT': '',
    }
}

MEDIA_ROOT = '/home/carlos/workspace/radiothon/media/'
#MEDIA_URL = 'http://localhost:8000/radiothon/media/'
STATIC_ROOT = '/home/carlos/workspace/radiothon/static/'
#STATIC_URL = 'http://localhost:8000/radiothon/static/'
STATICFILES_DIRS = (
    "/home/carlos/workspace/radiothon/radiothon/static",
)
TEMPLATE_DIRS = (
    '/home/carlos/workspace/radiothon/templates',
    '/home/carlos/workspace/radiothon/wuvt_ims/templates',
)
ADMIN_APPS = ('django.contrib.admin',
              'django.contrib.auth',
              'django.contrib.contenttypes',
              'django.contrib.messages',
              'django.contrib.sessions')
INSTALLED_APPS = INSTALLED_APPS + ADMIN_APPS + ('radiothon',)