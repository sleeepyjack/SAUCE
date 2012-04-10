<%inherit file="local:templates.master"/>

% if event:
<%def name="body_class()">navbar_left</%def>
% endif

<%def name="title()">
  Submissions
</%def>

<h2>Submissions</h2>

<h3>Your Submissions</h3>

<table>
  <tr>
    <th>ID</th>
    <th>Assignment</th>
    <th>Language</th>
    <th>Result</th>
    <th>Timestamp</th>
    <th>Runtime</th>
  </tr>
    %for submission in submissions:
    <tr>
        <th>${submission.link}</th>
        <td>${submission.assignment.link}</td>
        <td>${submission.language.name}</td>
        % if not submission.complete:
          <td>n/a</td>
        % else:
          <td>
		  % if submission.result:
		    <span class="green">ok</span>
		  % else:
		    <span class="red">fail</span>
		  </td>
		  % endif
         <td>${submission.date.strftime('%x %X')}</td>
         <td>${'%.3f sec' % submission.runtime}</td>
        % endif
        
    </tr>
    %endfor
</table>
  
% if submissions.pager:
  <p>${submissions.pager('Pages: $link_previous ~2~ $link_next')}</p>
% endif


