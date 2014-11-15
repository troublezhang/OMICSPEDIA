from django.shortcuts import render, render_to_response
from django.core.urlresolvers import reverse, reverse_lazy
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView
from .models import Tag
from posts.models import MainPost
from wiki.models import Page, PageRevision
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Create your views here.

class TagList(ListView):
#    model = Tag
    template_name = "tags/index.html"
    paginate_by = 2
    queryset = Tag.objects.filter(parent__isnull=True)


class TagCreate(CreateView):
    model = Tag
    template_name = "tags/tag_create.html"
    fields = ['name','wiki_page','categories']

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TagCreate, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TagCreate,self).get_context_data(**kwargs)
        if self.kwargs['parent_name'] !='':
            tag = Tag.objects.get(name = self.kwargs['parent_name'])
            message = ""
            while tag:
                message = tag.name+'/' + message
                tag = tag.parent
            message = "This tag will be created under: " + message
        else:
            message = '''Tips: if you want to create a new tag nested under another tags,
                       please do that in the respective tag page.'''
        context['message'] = message
        return context

class TagEdit(UpdateView):
    model = Tag
    template_name = "tags/tag_edit.html"
    fields = ['name','wiki_page','categories','icon']

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TagEdit, self).dispatch(*args, **kwargs)
        
    def get_object(self):
        return Tag.objects.get(name=self.kwargs['name'].replace('_',' '))


class TagDetails(DetailView):
    template_name = 'tags/tag_detail.html'
    model = Tag
    def get_object(self):
        return Tag.objects.get(name=self.kwargs['name'])
    def get_context_data(self, **kwargs):
        context = super(TagDetails, self).get_context_data(**kwargs)
        tab = self.request.GET.get('tab')
        context['tab'] = tab
        context['tag_wiki'] = self.object.wiki_page
        context['wiki_list'] = self.object.page_set.all()
        if tab == 'Posts' or not tab:
            context['post_list'] = self.object.posts.all()

        return context

class TagDelete(DeleteView):
    model = Tag
    template_name = 'tags/tag_delete.html'
    success_url = reverse_lazy('tags:tag-index')
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TagDelete, self).dispatch(*args, **kwargs)
        
    def get_object(self):
        return Tag.objects.get(name=self.kwargs['name'])


def suggest_tags(request):
    context = RequestContext(request)
    suggest_tag_list = []
    contains = ''
    if request.method == 'GET':
            contains = request.GET['suggestion']
    suggest_tag_list = Tag.objects.get_tag_search_list(0, contains)
    return render_to_response('tags/tag_suggest_list.html', {'suggest_tag_list': suggest_tag_list, 'suggest':contains }, context)
