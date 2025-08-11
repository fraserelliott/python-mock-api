# How to set up

1. Clone the repo
2. Open the folder in VS Code
3. `cd frontend` or `cd backend`, depending on which you are working on
4. Run `npm run setup`. This will install all dependencies and set up the Python virtual environment.
5. Edit the `.env` file in the backend folder with your MySQL configuration.
6. Set up mysql:
```bash
cd backend
mysql -u root -p
```
```sql
source schema.sql;
```


# How to run for testing

There are pre-made scripts to ensure the correct servers run and URLs are set for API access.  
Please do **not** change these; if anything isn't working or you're unsure, ask Fraser.

**For Frontend:**
1. Use `npm run dev-mock` while the backend is still in development.
2. Use `npm run dev-backend` once you get the go-ahead.

**For Backend:**
- Use `npm run dev`

# Server GUI Notes

- Failure Simulation: Use the dropdowns to trigger simulated failures on specific routes or middleware. This helps test error handling in the frontend.

- Reset Button: Reloads the server data from the JSON files. The server keeps data in memory during runtime and does not write changes back to JSON files, so resetting restores the initial dataset.


# Notes on Foreign Keys and Joined Data

Some dataset fields, like `post_id` or `user_id`, appear in mock data as placeholders to show relationships.  
**Please do not** use these fields to trigger extra fetches in the UI.

In the real backend, these relationships will be resolved and joined automatically, so the frontend receives fully joined data.

If you notice any foreign-key-like fields causing confusion or requiring additional fetching, please raise this with Fraser. This helps us improve the placeholders once the backend is complete. These are listed in the `Datasets` section of this document.

If you have any doubts, ask — these can be quickly checked in the generation config.


# Branches and Pull Requests

Please use a branch for the issue you've assigned yourself to and only upload here, never to the main branch. Once you have finished working on it, create a pull request and ensure you include a link to the issue in the request template. This will then be reviewed for consistency with the rest of the codebase, merged and any constructive feedback provided.

If you have any issues working on your branch or want any help, please feel free to ask straight away. We'll always be able to help you and will ensure a smooth project by tackling any problems together.


# Style Notes

There are some css variables in index.css, please use these across the project for consistent styling. If you are looking to change these, please discuss with the group so we can all agree on the project's direction.


# Contexts

If you feel there's anything that should be available across the whole project e.g. the username of the logged in user, check the contexts folder to see what's there. If it's not in here, please raise to the group and this can be created to stay consistent and have this available for everyone.


# Development Notes

The following section is auto-generated from the current API and dataset configurations to provide up-to-date information on endpoints, middleware, and datasets.
