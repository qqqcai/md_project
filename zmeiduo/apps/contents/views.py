from django.shortcuts import render
from django.views import View


class IndexView(View):
    """他们说这里提供首页广告，不知道是啥"""

    def get(self, request):
        """提供首页广告界面"""
        return render(request, "index.html")
