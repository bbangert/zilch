${next.body()}
<%def name="title()">${parent.title()} - Groups</%def>
<%def name="breadcrumbs()">${parent.breadcrumbs()} &gt; <a href="${request.application_url}/group/">Groups</a></%def>
<%inherit file="/layout.mak"/>
