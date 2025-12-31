# Product requirements

We are building an interactive web app for data visualization. Here is how the app should work:

1. the main UI is a prompt box on a web browser
2. the backend provides a general data API that runs a SQL and return a small subset of output (<100 lines) immediately
3. On the UI, user describes their ask; the agent will a) understand and translate the ask into executable tasks such as SQL and send requests to the backend APIs; while waiting for the API response, the agent will also generate appropriate UI code on the spot; once the output is back, renders the generated UI with the output on the web browser
4. user will also be able to iterate the UI with / without re-sending the request.
5. user can also choose to parametrize the conversation as a template for later use or sharing with others.

We can assume the data APIs are provided elsewhere.
