# Blender MCP Installation Guide

This guide provides enterprise-level instructions for installing the `blender-mcp` addon and its associated components to ensure stability and full functionality.

There are two primary components to the `blender-mcp` system:

1.  **The `blender-mcp` Python Server**: An external Python application that agents connect to.
2.  **The Blender Addon**: A plugin running inside Blender that the Python server communicates with.

Both must be installed and running correctly.

## Step 1: Install the `blender-mcp` Python Server & Dependencies

This step ensures that the core server and all its Python dependencies (like `structlog`) are installed correctly in your environment.

1.  **Open a Terminal or Command Prompt**:
You will need a terminal to install the Python package.

2.  **Navigate to the Project Directory**:
    ```sh
    cd path/to/your/blender-mcp
    ```

3.  **Install the Package in Editable Mode**:
    This command uses `pip` to install the project. The `-e` flag (for "editable") is recommended for development, as it allows your changes to the source code to be immediately available without reinstalling.

    ```sh
    pip install -e .[dev]
    ```

    This command will:
    - Read the `pyproject.toml` file.
    - Install all required dependencies, including `mcp`, `pydantic`, and `structlog`.
    - Install the development dependencies like `pytest`.
    - Make the `blender-mcp` command available in your terminal.

## Step 2: Install the Addon in Blender

This addon is the bridge between the Python server and Blender.

1.  **Open Blender**.
2.  Go to `Edit > Preferences > Add-ons`.
3.  Click the **Install...** button at the top-right.
4.  Navigate to the `blender-mcp` project directory and select the `addon.py` file.
5.  Click **Install Add-on**.
6.  After installation, find "Blender MCP" in your addon list (you can search for it) and **enable the checkbox** next to its name.

## Step 3: Start the Blender Server

Once the addon is enabled, you must start its internal server so that the external Python server can connect.

1.  In Blender, open the 3D Viewport.
2.  Press the `N` key to open the sidebar.
3.  Find and click on the **BlenderMCP** tab.
4.  You will see a panel with a "Status: Stopped" message.
5.  Click the **Start Server** button.

    - The status should change to **"Status: Running (no client)"**.
    - This indicates the addon is now listening for connections from the `blender-mcp` Python server.

## Step 4: Verify the Installation

Now you can run the connection test script to verify that both components are working and can communicate with each other.

1.  **Ensure the Blender server is running** (Step 3).

2.  **Open a new Terminal** and navigate to the project directory.

3.  **Run the test script**:
    ```sh
    python test_connection_fix.py
    ```

**Expected Output:**

If everything is configured correctly, you should see a success message for both the "Blender Addon Connection" and the "MCP Server Connection".

```
Blender MCP Connection Test
==================================================
Testing connection to Blender MCP addon at localhost:9876
Attempting to connect...
✓ Connection established

Test 1: Ping command
✓ Ping test passed
...

==================================================
Testing MCP Server Connection
==================================================
Attempting to connect to Blender via MCP server...
✓ MCP server connection established
...

==================================================
Test Summary:
Blender Addon Connection: ✓ PASS
MCP Server Connection: ✓ PASS

🎉 All connection tests passed! The blender-mcp setup is working correctly.
```

If the tests pass, the system is ready. Agents can now connect to the `blender-mcp` server and control Blender.

### Troubleshooting

-   **`Connection refused`**: This means the server inside Blender is not running. Go to the BlenderMCP panel in Blender and click "Start Server".
-   **`No module named '...'`**: This means the Python dependencies are not installed correctly. Re-run `pip install -e .[dev]` in your terminal.
-   **Firewall Issues**: Ensure that your system's firewall is not blocking connections on the port you are using (default is `9876`).
