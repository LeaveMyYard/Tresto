# Note 1 (Issues with playwright iterate -> only html exploration was useful)

- Investigation: with current implementation of playwright iterate, the model seems to generate different test code each time.
- This is the problem as it seems to walk in circles
- What I think would be better, is to rework this tool and to only keep the HTML investigation part.
- What I would like to do is to run the current test code and then to inspect the HTML of the page.
- This way the model will not be able to diverge from the initial test code.
- Additionally, I think just the html investigation should be better without the "report" part. Report functionality seemed to be loosing information.
- So we need to rewrite the playwright_iterate to html_explor


# Note 2 (Utilizing image input)

- Investigation: I've seen some agents that do things in the internet by using image input from the browser.
- I think this is a good idea to utilize for the tresto agent.
- We need to add ability for model to see the screenshot after the playwright test is finished (in addition to the html investigation)


# Note 3 (Automatically adding data-testid or other attributes)

- Investigation: Sometimes it is really hard for the model to write the correct selectors for the elements.
- I think it would be good to add ability for model to add data-testid or other attributes to the html investigation.
- Because this feature would change the user's code (and not only test), I think it should be configurable.