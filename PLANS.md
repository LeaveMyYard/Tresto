# Plans for future development

## Note 1 (Issues with playwright iterate -> only html exploration was useful)

```txt
DONE ✅
```

- Investigation: with current implementation of playwright iterate, the model seems to generate different test code each time.
- This is the problem as it seems to walk in circles
- What I think would be better, is to rework this tool and to only keep the HTML investigation part.
- What I would like to do is to run the current test code and then to inspect the HTML of the page.
- This way the model will not be able to diverge from the initial test code.
- Additionally, I think just the html investigation should be better without the "report" part. Report functionality seemed to be loosing information.
- So we need to rewrite the playwright_iterate to html_explore

## Note 2 (Utilizing image input)

```txt
DONE ✅
```

- Investigation: I've seen some agents that do things in the internet by using image input from the browser.
- I think this is a good idea to utilize for the tresto agent.
- We need to add ability for model to see the screenshot after the playwright test is finished (in addition to the html investigation)

## Note 3 (Automatically adding data-testid or other attributes)

```txt
Re-evaluate the idea
```

- Investigation: Sometimes it is really hard for the model to write the correct selectors for the elements.
- I think it would be good to add ability for model to add data-testid or other attributes to the html investigation.
- Because this feature would change the user's code (and not only test), I think it should be configurable.

## Note 4

```txt
DONE ✅
```

- Agent already works really good, but missing ability to see:
  - Console Logs of the browser
  - Screenshots right after the action is performed (sometimes a delay between the action and completing removes some information, like notifications)

## Note 5

```txt
IN PROGRESS 🚧
```

- It should be better to change "timestamp" to "time" in the recording, making it relative to the start of the recording

## Note 6

```txt
IN PROGRESS 🚧
```

- Add "Human in the loop" feature, persist all user inputs in the docstring

## Note 7

```txt
IN PROGRESS 🚧
```

- When working with harder tests, sometimes the model starts to break some previous code, when iterating on fixing the new code.
  - Make it split the big test into multiple smaller tests (for example by groupping stems in some functions)
  - Make it define and iteratively update the todo list, so it better understands

## Note 8

```txt
IN PROGRESS 🚧
```

- Add ability to prompt for some actions after a test creation is finished (for example, remove magic literal "australia" and allow any country to be found in the field)

## Note 9

```txt
DONE ✅
```

- We need to make model to impor tresto and use something like

```python
import tresto
from playwright.async_api import Page, expect

async def test_campaigns_error_missing_config(page: Page):
    await page.goto(tresto.config.url)
```

And then make it possible to store secrets using

```python
tresto.secrets["api_key"] = "1234567890"
```
