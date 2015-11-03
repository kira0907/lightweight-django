# Chapter 2 -- Stateless Web Application

- Django는 기자들이 쉽고 빠르게 웹용 콘텐츠를 제작할 수 있게 하기 위해  2005년 World Online이라는 곳에서 만들어 짐.
- 그 이후로 워싱턴포스트, 가디언 등 주로 언론사에서나 CMS(content management system)의 목적으로 사용되어 왔음.
- 최근 들어 NASA 등에서 프레임워크로 활용하면서, 그 저변을 확대해나가고 있는 중임.

## Why Stateless?
- Stateless -- 서버로 들어오는 request들이 이전 request들에 대해 독립적임을 의미함. (http 또한 stateless protocol임)
- Django 같은 프레임워크들은 쿠키나 다른 방법을 활용하여, 동일한 클라이언트가 보낸 요청들을 연관지음.
- 따라서 사용자 인증 등을 해야 할 경우 모든 요청에 해당 인증을 위한 정보를 같이 보내야 함.

## Reusable Apps vs. Composable Services
- 어느 Django 프로젝트에서나 재사용될 수 있는 어플리케이션을 만드는 것은 대규모 웹사이트의 경우 architectural structure를 복잡하게 만듦.
- 따라서 대규모 웹사이트를 소규모의 서비스로 만들고, 이들 서비스 간에 communicate 하도록 하는 것이 한 방법임.
- REST API와 같은 stateless component들은 이러한 목적을 달성하기에 좋음.


## Placeholder Image Server
- 일반적인 placeholder image service는 이미지의 사이즈, 색상, 이미지내 텍스트 등을 URL로부터 받아옴
- 이 때, 이미지를 만들기 위한 모든 정보는 URL에 담겨있고, 또 사용자 인증 등의 필요도 적으므로, stateless application의 예제로 적합함.

### Views

The first part renders placeholder images based on the request.
The second part renders the home page content (html).

```python
def placeholder(request, width, height):
    return HttpResponse('Ok')
def index(request):
    return HttpResponse('Hello World')
```

### URL Patterns

Parameters width and height are captured by the URL and passed to the view.
- '?P' = named groups <width> and <height>
- '[0-9]' = integers from 0 to 9
- '+' = match 1 or more

```python
urlpatterns = (
    url(r'^image/(?P<width>[0-9]+)x(?P<height>[0-9]+)/$', placeholder, name='placeholder'),
    url(r'^$', index, name='homepage'),
)
```
URL example: /image/30x25/

## Placeholder view

Forms are used to:
- validate POST and GET
- validate values from URL
- validate values stored in cookies

The first thing the view should do is validate the requested image size.
If the form is valid, then the height and width can be accessed in the form's cleaned_data attribute.
At this point, the height and width will be converted to integers, between 1 and 2000.
If the form is invalid, the view returns HttpResponseBadRequest (400).

```python
from django import forms
from django.conf.urls import url
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse, HttpResponseBadRequest

class ImageForm(forms.Form):
    height = forms.IntegerField(min_value=1, max_value=2000)
    width = forms.IntegerField(min_value=1, max_value=2000)

def placeholder(request, width, height):
    form = ImageForm({'height': height, 'width': width})
    if form.is_valid():
        height = form.cleaned_data['height']
        width = form.cleaned_data['width']
        return HttpResponse('Ok')
    else:
        return HttpResponseBadRequest('Invalid Image Request')
```

### Image Manipulation

In order to handle image manipulation, install Pillow ($ pip install Pillow).

Creating an image with Pillow requires two arguments: color mode and image size (tuple).
This view uses RGB mode and form's cleaned data values as size.
The third optional argument sets the color of the image (default: black).

```python
from io import BytesIO
from PIL import Image

class ImageForm(forms.Form):
    height = forms.IntegerField(min_value=1, max_value=2000)
    width = forms.IntegerField(min_value=1, max_value=2000)
    def generate(self, image_format='PNG'):
        '''
        'generate' method has been added to the 'ImageForm' class
        to encapsulate the logic of building the image.
        It takes one argument for the image format (default: png) and
        returns the image content as bytes.
        '''
        height = self.cleaned_data['height']
        width = self.cleaned_data['width']
        image = Image.new('RGB', (width, height))
        '''
        Using width and height given by the URL and validated by the form,
        a new image is constructed using Image class from Pillow.
        '''
        content = BytesIO()
        image.save(content, image_format)
        content.seek(0)
        return content

def placeholder(request, width, height):
    form = ImageForm({'height': height, 'width': width})
    if form.is_valid():
        image = form.generate()
        return HttpResponse(image, content_type='image/png')
        '''
        View calls form.generate() to get the image, and
        the bytes for the image are then used to construct the response body.
        '''
    else:
        return HttpResponseBadRequest('Invalid Image Request')
```

The form then validates the size to prevent requesting too large of an image and consuming too many resources on the server.
Once the image has been validated, the view successfully returns the PNG image for the requested width and height.
The image content is sent to the client without writing it to the disk.

ImageDraw module from Pillow allows you to add text to image.

```python
from io import BytesIO
from PIL import Image, ImageDraw

class ImageForm(forms.Form):
    height = forms.IntegerField(min_value=1, max_value=2000)
    width = forms.IntegerField(min_value=1, max_value=2000)
    def generate(self, image_format='PNG'):
        height = self.cleaned_data['height']
        width = self.cleaned_data['width']
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        text = '{} X {}'.format(width, height)
        textwidth, textheight = draw.textsize(text)
        if textwidth < width and textheight < height:
            texttop = (height - textheight) // 2
            textleft = (width - textwidth) // 2
            draw.text((textleft, texttop), text, fill = (255, 255, 255))
        content = BytesIO()
        image.save(content, image_format)
        content.seek(0)
        return content
```

### Adding Caching

1. Server-side caching: Django's cache utilities
  - Trades memory usage to store the cached values while saving the CPU cycles
  - Cache key is generated depending on width, height and image format.
  - generate now checks the cache to see if the image is already stored.
  - A newly generated image is cached for 1 hour
- Django defaults to using a process-local, in-memory cache
  - Other backend, such as Memcached or the file system, can be used by configuring CACHES setting.

```python
from django.core.cache import cache

class ImageForm(forms.Form):
    height = forms.IntegerField(min_value=1, max_value=2000)
    width = forms.IntegerField(min_value=1, max_value=2000)
    def generate(self, image_format='PNG'):
        height = self.cleaned_data['height']
        width = self.cleaned_data['width']
        key = '{}.{}.{}'.format(width,height,image_format)
        content = cache.get(key)
        if content is None:
            image = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(image)
            text = '{} X {}'.format(width, height)
            textwidth, textheight = draw.textsize(text)
            if textwidth < width and textheight < height:
                texttop = (height - textheight) // 2
                textleft = (width - textwidth) // 2
                draw.text((textleft, texttop), text, fill = (255, 255, 255))
            content = BytesIO()
            image.save(content, image_format)
            content.seek(0)
            cache.set(key,content,60 * 60)
        return content
```

2. Client-side caching
  - etag decorator for generating and using ETag headers for the view
  - Image is generated the first time browser requests
  - If browser requests with a matching ETag, browser receives 304 Not Modified response
  - Then the browser uses the image from the cache
  - Middlewares?

```python
import hashlib
import os

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import etag

def generate_etag(request, width, height):
    content = 'Placeholder: {0} x {1}'.format(width, height)
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

@etag(generate_etag)
```

## Creating the Home Page View

Settings:
- INSTALLED_APPS
- TEMPLATE_DIRS
- STATICFILES_DIRS
- STATIC_URL

### Adding Static and Template Settings

Directory:
placeholder/
    placeholder.py
    templates/
        home.html
    static/
        site.css

```python
settings.configure(
    DEBUG=DEBUG,
    SECRET_KEY=SECRET_KEY,
    ALLOWED_HOSTS=ALLOWED_HOSTS,
    ROOT_URLCONF=__name__,
    MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ),
    INSTALLED_APPS=(
        'django.contrib.staticfiles',
    ),
    TEMPLATE_DIRS=(
        os.path.join(BASE_DIR, 'templates'),
    ),
    STATICFILES_DIRS=(
        os.path.join(BASE_DIR, 'static'),
    ),
    STATIC_URL='/static/'
)
```
### Home Page Template and CSS
home.html
```html
{% load staticfiles %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Django Placeholder Images</title>
    <link rel="stylesheet" href="{% static 'site.css' %}" type="text/css">
</head>
<body>
    <h1>Django Placeholder Images</h1>
    <p>This server can be used for serving placeholder images for any web page.</p>
    <p>To request a placeholder image of a given width and height, simply include an image with the source pointing to <b>/placeholder/&lt;width&gt;x&lt;height&gt;/</b> on this server such as:</p>
    <pre>
        &lt;img src="{{ example }}" &gt;
    </pre>
    <h2>Examples</h2>
    <ul>
        <li><img src="{% url 'placeholder' width=50 height=50 %}"></li>
        <li><img src="{% url 'placeholder' width=100 height=50 %}"></li>
        <li><img src="{% url 'placeholder' width=50 height=100 %}"></li>
    </ul>
</body>
</html>
```

site.css
```css
body {
    text-align: center;
}

ul {
    list-type: none;
}

li {
    display: inline-block;
}
```

Update index view in placeholder.py to render the template:
- Updated index view builds an example URL by reversing the placeholder view and passes it to the template context.
- home.html template is rendered using the render shortcut.

```python
from django.core.urlresolvers import reverse
from django.shortcuts import render

def index(request):
    example = reverse('placeholder', kwargs={'width':50, 'height':50})
    context = {
        'example': request.build_absolute_uri(example)
    }
    return render(request, 'home.html', context)    
```

### Completed Project
