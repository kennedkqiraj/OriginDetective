# How to Run This Application in Google Cloud Shell

This guide provides the step-by-step instructions to set up and run the OriginDetective application from a fresh start in a Google Cloud Shell environment.

## Prerequisites

- You have access to a Google Cloud Shell terminal.
- The project code has been cloned into your environment.

## Step-by-Step Instructions

1.  **Navigate to the Project Directory**

    Open your Cloud Shell terminal and change into the application's root folder.
    ```bash
    cd /path/to/your/OriginDetective
    ```

2.  **Create and Activate a Virtual Environment**

    It's crucial to use a virtual environment to manage project dependencies without affecting the system.

    ```bash
    # Create the virtual environment (only needs to be done once)
    python3 -m venv venv

    # Activate the environment (do this every time you open a new terminal)
    source venv/bin/activate
    ```
    Your terminal prompt should now be prefixed with `(venv)`.

3.  **Install Dependencies**

    This project uses `uv` to manage packages. The `uv.lock` file contains the exact versions of all required libraries. Install them by running:

    ```bash
    uv sync
    ```

4.  **Run the Application**

    We use Gunicorn, a production-ready web server, to run the Flask application.

    ```bash
    gunicorn --bind 0.0.0.0:8080 app:app
    ```

5.  **Preview Your Application**

    Google Cloud Shell provides a convenient way to view your running web app.

    - In the top-right corner of the Cloud Shell window, click the **Web Preview** button.
    - Select **Preview on port 8080**.

To stop the server, go back to the terminal and press `Ctrl+C`.