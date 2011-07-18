<%def name="display_date(date)">
<%
    diff = datetime.utcnow() - date
    now = pytz.UTC.localize(datetime.utcnow()).astimezone(request.timezone)
    date = pytz.UTC.localize(date).astimezone(request.timezone)
%>
% if diff.days < 3:
${distance_of_time_in_words(date, now, granularity='minute')} ago
% else:
${date.strftime('%x %X')}
% endif
</%def>
<%!
import pytz
from datetime import datetime
from webhelpers.date import distance_of_time_in_words
%>
