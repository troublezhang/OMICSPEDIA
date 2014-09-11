from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericRelation 
from django.utils import timezone
from django.contrib.auth.models import User
import markdown
from utils import diff_match_patch
from utils.models import AbstractBaseRevision

# Create your models here.

# Ideally, every tag should have a wiki,
# but not every wiki should have a tag.
# so it may be oneToOne relationship from Tag to Wiki Page.
class Page(models.Model):

    title = models.CharField(_("title"), max_length=255, unique=True)
    tags = models.ManyToManyField("tags.Tag",blank=True)
    wiki_votes = GenericRelation("utils.Vote")
    current_revision = models.OneToOneField('PageRevision', blank=True, null=True, verbose_name=_('current revision'),
                                            related_name = "revision_page")
    def __unicode__(self):
        return self.title

    def get_title(self):
        return self.title.replace(" ", "_")


    def get_vote_count(self):
        return self.wiki_votes.filter(choice=1).count() - self.wiki_votes.filter(choice=-1).count()

    def get_absolute_url(self):
        return reverse('wiki:wiki-detail', kwargs = {'title': self.get_title()})

class PageRevision(AbstractBaseRevision):

    page = models.ForeignKey(Page, on_delete = models.CASCADE, verbose_name=_("page"))
    total_chars = models.IntegerField(_('total_chars'))
    added_chars = models.IntegerField(_('added_chars'))
    deleted_chars = models.IntegerField(_('deleted_chars'))

    def __unicode__(self):
        return self.page.title+"_revision_"+str(self.revision_number)


    def save(self, *args, **kwargs):
        if not self.revision_number:
            try:
                previous_revision = self.page.pagerevision_set.latest()
                self.revision_number = previous_revision.revision_number + 1
            except PageRevision.DoesNotExist:
                self.revision_number = 1
        self.cal_add_delete_chars()
        super(PageRevision, self).save(*args, **kwargs)

    def get_pre_revision(self):
        try:
            return PageRevision.objects.get(revision_number = self.revision_number - 1, page = self.page)
        except PageRevision.DoesNotExist:
            return

    def cal_add_delete_chars(self):
        if self.revision_number == 1:
            text1 = ""
        else:
            text1 = self.get_pre_revision().content
        text2 = self.content 
        func = diff_match_patch.diff_match_patch()
        diff = func.diff_main(text1, text2)
        added = 0
        deleted = 0
        for (sign, frag) in diff:
            if sign == 1:
                added += len(frag)
            elif sign == -1:
                deleted += len(frag)
        self.added_chars = added
        self.deleted_chars = deleted
        self.total_chars = len(text2)
    class Meta:
        get_latest_by= 'revision_number'

class PageComment(models.Model):
    # the status of the comment
    INITIALIZED, PROGRESS, PENDING, CLOSED = range(4)
    STATUS_CHOICE = [(INITIALIZED, "initialized"), (PROGRESS,"in progress"), (PENDING,"close pending"), (CLOSED,"closed")]
    status = models.IntegerField(choices=STATUS_CHOICE, default=INITIALIZED)
    # the type of the comment; this can be substitute as a subtype of issues. 
    ISSUE, REQUEST, DISCUSS = range(3)
    COMMENT_TYPE_CHOICE = [(ISSUE, "issue"), (REQUEST, "request"), (DISCUSS, "discuss")]
    comment_type = models.IntegerField(choices=COMMENT_TYPE_CHOICE, default="discuss")
    # This is only required when the user report issue
    GRAMMER, WIKILINK, EXPAND, CHECK_REFERENCE, ADD_REFERENCE, IMAGE, LEAD, NEW_INFO = range(8)
    ISSUE_CHOICE = [(GRAMMER,'fix spelling and gramma'),
            (WIKILINK, 'fix wikilink'), (EXPAND, 'expand short article'),
            (CHECK_REFERENCE, 'check reference'), (ADD_REFERENCE, 'add reference'),
            (IMAGE, 'add image'), (LEAD, 'Improve lead section'),
            (NEW_INFO,'add new information')]
    issue = models.IntegerField(choices=ISSUE_CHOICE, null=True)
    # the details of the comment
    detail = models.TextField(verbose_name = _("detail"), blank=True)
    page = models.ForeignKey("Page", related_name="comments")
    init_revision = models.ForeignKey("PageRevision", related_name="comment_init",blank=True,null=True)
    # instead of final version, show revised version. 
    final_revision = models.ForeignKey("PageRevision", related_name="comment_closed",blank=True,null=True)
    author = models.ForeignKey(User, verbose_name=_("author"))
    created = models.DateTimeField(_("created date"))
    modified = models.DateTimeField(_("modifed date"),auto_now=True)
    
    def __unicode__(self):
        return self.get_comment_type_display() + ': ' + self.get_issue_display()
        
    def get_absolute_url(self):
        return reverse('wiki:wiki-comment', kwargs = {'title': self.page.get_title()})
        
    def get_status_class(self):
    # INITIALIZED, PROGRESS, PENDING, CLOSED = range(4)
        dict = {self.INITIALIZED:"btn-danger", self.PROGRESS:"btn-info", 
        self.PENDING:"btn-success", self.CLOSED:"btn-default"}
        return dict[self.status]
# --------- #
# a page can have several sections, instead of just one giant
# piece of content, this will make editing more convenient.
# setting it up now, but will not use it in demonstration.

