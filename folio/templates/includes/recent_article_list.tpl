% last_date = None
% for _ in wiki.recent_articles():
% if last_date != _.short_date:
<div class="wiki-recent-date">{{_.short_date}}</div>
% last_date = _.short_date
% end
<div class="wiki-recent-article{{' wiki-recent-article-editing' if _.opened_by else ''}}"><a {{!jsnavlink}} title="{{_.title}}{{' (Editing)' if _.opened_by else ''}}" href="{{_.link}}">{{_.title}}</a></div>
% end