% if 'style' in locals() and style:
<style>{{!style}}</style>
% end
% article_text = article.formatted
% article_title = article.new_title if article.new_title else article.title
% if article.get_metadata('@hide-title') is None:
<h1>
  % if not article.id:
  {{article_title}}
  % else:
  <a href="{{article.link}}">{{article_title}}</a>
  % end
  <span class="float-right" style="font-size: .5em; margin-top: 1em">
    <a title="See article revision history" href="{{article.history_link}}"><span class="oi oi-calendar"></span></a>
    % if not article.revision_of:
    <a id="article-edit-link" title="Edit article (Ctrl-E)" href="{{article.edit_link}}"><span class="oi oi-pencil"></span></a>
    % end
  </span>
</h1>


% if article.revision_of:
<div class="wiki-revisions">
  <span class="badge badge-warning">Revision of <a
      href="{{article.revision_of.link}}">{{article.revision_of.title}}</a></span>
</div>
% end

% if article.draft_of:
<div class="wiki-draft">
  <span class="badge badge-warning">Draft of <a href="{{article.draft_of.link}}">{{article.draft_of.title}}</a></span>
</div>
% end

<div class="wiki-tags">
  % if article.exists_as_tag:
  <a title="This page is also a tag; see all articles with this tag" href="{{article.exists_as_tag.link}}"><span class="badge badge-secondary">{{article.exists_as_tag.title}}</span></a>
  % end
  % for tag_ref in article.tags_alpha:
    % tag_article = tag_ref.article_exists
    % if tag_article:
    <a title="See article with this tag name" href="{{tag_article.link}}"><span class="badge badge-success">{{tag_article.title}}</span></a>
    % elif tag_ref.is_system_tag:
    <a title="See all articles with this system tag" href="{{tag_ref.link}}"><span class="badge badge-danger">{{tag_ref.title}}</span></a>
    % else:
    <a title="See all articles with this tag" href="{{tag_ref.link}}"><span class="badge badge-primary">{{tag_ref.title}}</span></a>
    % end
  % end
</div>
<small><b>{{article.author.name if article.author else ''}}</b> {{article.formatted_date}}</small>
<hr />

% if article.has_tag('@form'):
% new_article = article.__class__(title='Untitled',wiki=article.wiki, author=article.author)
<div class="wiki-create-from-template">
<a href="{{new_article.form_creation_link(article)}}"><button type="button" class="btn btn-sm btn-success">Create new article from this form article</button></a><hr/>
</div>
% end

% end

<div class="wiki-article-container">
  % if article_text:
  {{!article_text}}
  % else:
  [<i>This article is blank.</i>]
  % end
</div>