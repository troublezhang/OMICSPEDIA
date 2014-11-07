from django.shortcuts import render
from django.views.generic import DetailView, ListView, TemplateView, UpdateView, CreateView, DeleteView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils import timezone

# models 
from .models import MainPost, ReplyPost, MainPostRevision, ReplyPostRevision
from .models import MainPostComment, ReplyPostComment
# forms
from .forms import MainPostForm, MainPostRevisionForm
# to mask the manytomany field message. 
MainPostForm.base_fields['tags'].help_text = 'Please type your tags'
MainPostRevisionForm.base_fields['tags'].help_text = 'Please type your tags'
# Create your views here.


class IndexView(ListView):
    model = MainPost
    template_name = "posts/index.html"
    context_object_name = "post_list"

    def get_queryset(self):
        tab = self.request.GET.get('tab')
        if tab =="Latest":
            return MainPost.objects.order_by('-last_modified')
        elif tab =="Votes":
            return MainPost.objects.order_by('-vote_count')
        elif tab =="Unanswered":
            return MainPost.objects.filter(reply_count__exact=0)
        else:
            return MainPost.objects.all()
    def get_context_data(self,**kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['tab'] = self.request.GET.get('tab')
        return context

class MainPostNew(CreateView):
    template_name = "posts/post_new.html"
    form_class = MainPostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        new_revision = MainPostRevision(content=self.request.POST['content'], post=form.instance,
                author=self.request.user)
        new_revision.save()
        form.instance.current_revision=new_revision
        return super(MainPostNew, self).form_valid(form)




class MainPostEdit(UpdateView):
    form_class = MainPostRevisionForm
    template_name = 'posts/post_new.html'
    def get_object(self):
        return MainPost.objects.get(pk=self.kwargs['pk'])

    def get_form(self, form_class):
        kwargs = self.get_form_kwargs()
        kwargs['initial'].update({'content':self.object.current_revision.content})
        return form_class(**kwargs)

    def form_valid(self, form):
        new_revision = MainPostRevision(content=self.request.POST['content'],
                       revision_summary=self.request.POST['summary'], post=self.object,
                       author=self.request.user)
        new_revision.save()
        self.object.current_revision=new_revision
        self.object.save()
        return super(MainPostEdit, self).form_valid(form)


class PostDetails(DetailView):
    template_name = "posts/post_detail.html"
    model = MainPost
    context_object_name = "mainpost"

    def get_object(self):
        obj = super(PostDetails, self).get_object()
        MainPost.update_post_views(obj, request=self.request)
        return obj
    def get_context_data(self, **kwargs):
        context = super(PostDetails, self).get_context_data(**kwargs)
        context['replypost_list'] = ReplyPost.objects.filter(mainpost=context['mainpost'])
        return context
    #need to display everything in the same subject.


class ReplyPostNew(CreateView):
    model = ReplyPost
    fields = []
    template_name = 'posts/replypost_new.html'
    #will need to redirect to the main post; will implement later.
    def get_success_url(self):
        return self.object.get_absolute_url()
    def get_context_data(self, **kwargs):
        context = super(ReplyPostNew, self).get_context_data(**kwargs)
        context['mainpost'] = MainPost.objects.get(id=self.kwargs['mainpost_id'])
        return context

    def form_valid(self, form):
        form.instance.mainpost = MainPost.objects.get(pk = int(self.kwargs['mainpost_id']))
        form.instance.author = self.request.user
        form.save()
        new_revision = ReplyPostRevision(content=self.request.POST['content'], post=form.instance, 
                        author=self.request.user)
        new_revision.save()
        form.instance.current_revision=new_revision
        return super(ReplyPostNew, self).form_valid(form)

class ReplyPostEdit(UpdateView):
    model = ReplyPost
    fields = []
    template_name = 'posts/replypost_edit.html'

    def form_valid(self, form):
        new_revision = ReplyPostRevision(content=self.request.POST['content'], 
                       revision_summary=self.request.POST['summary'], post=self.object, 
                       author=self.request.user)
        new_revision.save()
        self.object.current_revision=new_revision
        self.object.save()
        return super(ReplyPostEdit, self).form_valid(form)

class ReplyPostDelete(DeleteView):
    model = ReplyPost
    template_name = 'posts/replypost_delete.html'
    #success_url = reverse_lazy('posts:post-index')
    def get_success_url(self):
        return self.object.get_absolute_url()

class MainPostHistory(ListView):
    model = MainPostRevision
    template_name = "posts/post_revision_history.html"
    context_object_name = "revision_list"

    def get_queryset(self):
        return MainPostRevision.objects.filter(post__id = self.kwargs['pk']).order_by('-modified_date')

class ReplyPostHistory(ListView):
    model = ReplyPostRevision
    template_name = "posts/post_revision_history.html"
    context_object_name = "revision_list"

    def get_queryset(self):
        return ReplyPostRevision.objects.filter(post__id = self.kwargs['pk']).order_by('-modified_date')


