% include('includes/header.tpl')

<main role="main" class="container-wiki">

    <div id="article-row" class="row">
        <div id="article-col" class="col">

            % include('includes/messages.tpl')

            <h1>Search {{wiki.title}}</h1>

            <form method="POST">

                <div id="wiki-search" class="form-group">
                    <label for="search_query">Search for:</label>
                    <input autofocus="autofocus" class="form-control form-control-lg"
                        placeholder="Any string of characters" id="search_query" name="search_query"
                        value="{{search_query}}">
                </div>

                <div id="wiki-buttons">

                    <span class="float-right">
                        <a href="{{wiki.link}}">
                            <button type="button" class="btn btn-sm btn-warning">Quit searching</button>
                        </a>
                    </span>

                    <button type="submit" name="search" value="search" class="btn btn-sm btn-success">Search</button>

                </div>
                <hr />
            </form>

            % # TODO: move this back into the search function as it's getting too complex to show here

            % if search_results:
                % for result_description, result_type, result_set in search_results:
                    <h2>{{result_description}}:</h2>
                    % if not result_set.count():
                        No results found.
                    % else:
                        % if result_description == "Article contents":
                            % for result in result_set:
                                % extract_position_start = result.content.find(search_query)
                                % if extract_position_start == -1: continue
                                % end
                                {{!result_type.format(result=result)}}
                                % content_length = len(result.content)                                
                                % extract_position_end = extract_position_start+len(search_query)
                                <p>... {{result.content[max(0, extract_position_start-30):extract_position_start]}}<b><a
                                    href="{{result.link}}">{{search_query}}</a></b>{{result.content[extract_position_end:min(content_length, extract_position_end+30)]}} ...
                                </p>
                            % end
                        % else:
                            % for result in result_set:
                                {{!result_type.format(result=result)}}
                            % end
                        % end
                    % end
                <hr />
                % end
            % end

        </div>
        <div id="sidebar" class="sidebar-col">
            % include('includes/sidebar.tpl')
        </div>
    </div>

</main>

% include('includes/footer.tpl')