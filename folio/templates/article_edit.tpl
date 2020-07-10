% include('includes/header.tpl')

<main role="main" class="container-wiki">

    <div class="row">
        <div id="left-col" class="col">

            % include('includes/messages.tpl')

            % article_title = article.title
            % if article.new_title:
                % article_title = article.new_title
            % else:
                % if article.draft_of:
                % article_title = article.draft_of.title
                % end
            % end

            <form method="POST" data-dirty="false" id="save-form" class="form-compact">

                <div id="editor-title" class="form-group">
                    <input class="form-control form-control-lg" id="article_title" name="article_title"
                        data-original="{{article_title if article.id is not None else ''}}" value="{{article_title}}">
                </div>

                <!--

                % if article.draft_of and article_title != article.draft_of.title:

                <div id="editor-rename-checkbox-div" class="form-group form-check">
                    <input type="checkbox" class="form-check-input" id="rename-links" name="rename-links" checked>
                    <label class="form-check-label" for="rename-links">Update all links to this article</label>
                </div>

                % end

                -->

                <div id="editor-controls" class="form-group">

                    % if article.id is not None:

                    <a href="#" id="btn_toggle_preview" title="Toggle preview (Ctrl+P)"><span
                            class="oi button-oi oi-eye"></span></a>
                    <a href="#" id="btn_toggle_bold" title="Bold selection (Ctrl+B)"><span
                            class="oi button-oi oi-bold"></span></a>
                    <a href="#" id="btn_toggle_ital" title="Italicize selection (Ctrl+I)"><span
                            class="oi button-oi oi-italic"></span></a>

                    <a href="#" id="btn_insert_link" title="Insert article link (Ctrl+L)"><span
                            class="oi button-oi oi-link-intact"></span></a>
                    <!-- <a href="#" title="Insert external link (Ctrl+K)"><span
                            class="oi button-oi oi-external-link"></span></a> -->
                    <a href="#" id="btn_insert_media" title="Insert media (Ctrl+M)"><span
                            class="oi button-oi oi-image"></span></a>
                    <a href="#" id="btn_edit_metadata" title="Edit article metadata (Ctrl-Shift-M)"><span
                            class="oi button-oi oi-info"></span></a>
                    <a href="#" id="btn_insert_tag" title="Edit article tags (Ctrl-G)"><span
                            class="oi button-oi oi-tags"></span></a>

                    % else:
                    <p></p>
                    % end

                </div>

                <div id="editor-text" class="form-group"><textarea class="form-control" id="article_content"
                        name="article_content" rows="10">{{!article.content}}</textarea></div>
                <div id="editor-buttons">
                    <div class="row">
                        <div class="col-6">
                            % if article.id is not None:
                            <button type="button" title="Save draft and continue editing (retain edit lock) (Ctrl-S)"
                                name="save" id="save-button" value="save" class="btn btn-sm btn-success">Save</button>
                            % else:
                            <button type="submit" title="Save and create article" name="save" id="save-button"
                                onclick="clearDirty();" value="save" class="btn btn-sm btn-success">Save and create
                                article</button>
                            % end

                            % if article.id is not None:
                            <button type="submit" id="save-and-exit-button"
                                title="Save draft and release edit lock. (Shift-Ctrl-S)" name="save" value="exit"
                                onclick="clearDirty();" class="btn btn-sm btn-info">Save and exit</button>
                            <button type="submit" id="save-and-publish-button"
                                title="Save and close draft, and update article with draft. (Alt-Shift-S)"
                                onclick="clearDirty();" name="save" value="publish"
                                class="btn btn-sm btn-primary">Publish</button>
                            <button type="submit"
                                title="Update article with draft, and create a revision from the current published version."
                                onclick="clearDirty();" name="save" value="revise"
                                class="btn btn-sm btn-dark">Version</button>
                            % end
                        </div>
                        <div class="col-6" style="text-align: right;">
                            % if article.id is not None:
                            <button type="submit" name="save" value="discard" title="Discard all changes in draft."
                                class="btn btn-sm btn-secondary">Discard draft</button>

                            <a href="{{article.delete_link}}"><button type="button" class="btn btn-sm btn-danger">Delete
                                    article</button></a>

                            <button type="submit" name="save" value="quit"
                                title="Close editor and release edit lock. Discards unsaved changes to the draft."
                                class="btn btn-sm btn-warning">Quit editing</button>
                            % else:
                            <a href="{{article.wiki.link}}"><button type="button" name="save" value="quit"
                                    title="Leave article creation." class="btn btn-sm btn-warning">Quit creating
                                    article</button></a>
                            % end
                        </div>
                    </div>
                </div>

            </form>

        </div>
        <div style="display:none; overflow-y:scroll; height: 95vh; margin-bottom: 16px; margin-right: 15px;"
            id="mid-col"></div>
        <div id="sidebar" class="sidebar-col">
            % include('includes/sidebar.tpl')
        </div>
    </div>

</main>

<div class="modal" id="edit-modal" tabindex="-1" role="dialog">
</div>

% include('includes/footer.tpl')
<script>
    articleTarget = "{{article.link}}";
    saveTarget = articleTarget + "/save";
    previewTarget = articleTarget + "/preview";
    apiTarget = "{{wiki.link}}/api";
    hasError = {{ has_error }};
    mediaPaste = "{{ wiki.media_paste_link }}";
</script>
<script src="/static/editor.js?0.0.6"></script>