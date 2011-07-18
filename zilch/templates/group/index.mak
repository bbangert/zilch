<h1>Recent Grouped Events</h1>

<section>
    <table width="100%">
        <thead>
            <tr>
                <th>Count</th>
                <th>Message</th>
                <th>Last Seen</th>
                <th>Tags</th>
                <th>Type</th>
                <th>First Seen</th>
            </tr>
        </thead>
        <tbody>
        % for group in groups:
        <tr>
            <td>${group.count}</td>
            <td><a href="${request.resource_url(request.context)}${group.id}">${group.message}</a></td>
            <td>${display_date(group.last_seen)}</td>
            <td>${group.tags}</td>
            <td>${group.event_type.name}</td>
            <td>${display_date(group.first_seen)}</td>
        </tr>
        % endfor
        </tbody>
    </table>
</section>
<%def name="javascript()">
${parent.javascript()}
<script>
$(document).ready(function() {
    $('section table tr').click(function(event) {
        event.stopPropagation();
        document.location = $(this).find('td a').attr('href');
        return false;
    });
});
</script>
</%def>
<%inherit file="layout.mak"/>
<%namespace file="/common.mak" import="display_date"/>