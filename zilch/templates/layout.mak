<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>${self.title()}</title>

        <link href="${request.application_url}/stylesheets/screen.css" media="screen, projection" rel="stylesheet" type="text/css" />
        <link href="${request.application_url}/stylesheets/print.css" media="print" rel="stylesheet" type="text/css" />
        <!--[if IE]>
            <link href="${request.application_url}/stylesheets/ie.css" media="screen, projection" rel="stylesheet" type="text/css" />
        <![endif]-->

        <!-- JavaScript -->
        <!--[if IE]><![endif]-->
        <!--[if lt IE 9]>
        <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
        <![endif]-->
    </head>
    <body>
        ${self.post_body()}
        <div>
            <header>
                <nav>${self.breadcrumbs()}</nav>
            </header>
            ${next.body()}
        </div>
        ${self.javascript()}
    </body>
</html>
<%def name="post_body()"></%def>
<%def name="title()">zilch</%def>
<%def name="javascript()">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.2/jquery.min.js"></script>
</%def>
<%def name="breadcrumbs()"><a href="${request.application_url}">Zilch</a></%def>
