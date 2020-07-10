% if not "messages" in locals():
% messages = None
% end

% if messages:
% for message in messages:
% if message:
{{!message}}
% end
% end
% end
<div class="alert-box" id="flash-message"></div>