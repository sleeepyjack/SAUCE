<%inherit file="local:templates.master"/>

<%def name="title()">
  Test
</%def>

<h2>Test</h2>

% if compilation:
  <h3>Compilation:</h3>
  % if compilation.returncode == 0:
    <p><img src="${tg.url('/images/ok.png')}" alt="success"/> Successful</p>
  % else:
    <p><img src="${tg.url('/images/error.png')}" alt="failed"/> Failed</p>
  % endif
% endif

% if results:
  <h3>Test runs:</h3>
  <p>${results.succeeded} / ${results.succeeded + results.failed} Tests successfully finished</p>
  <p>
  % for testrun in testruns:
    % if testrun.returncode == 0:
      <img src="${tg.url('/images/ok.png')}" alt="success"/>
    % else:
      <img src="${tg.url('/images/error.png')}" alt="failed"/>
    % endif
  % endfor
  </p>
% endif