from mcp.server.fastmcp import FastMCP
import sqlite3
import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse

DB_PATH = os.environ.get("DB_PATH", "medical_equipment.db")
PORT = int(os.environ.get("PORT", 8000))

mcp = FastMCP("Medical Equipment DB", host="0.0.0.0", port=PORT)

@mcp.tool()
def run_query(sql: str) -> str:
    """Run a read-only SQL SELECT query against the medical_equipments table and return the results."""
    if not sql.strip().lower().startswith("select"):
        return "Error: Only SELECT queries are allowed."
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql).fetchall()
        conn.close()
        return str([dict(r) for r in rows])
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_tables() -> str:
    """List all tables in the database."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    conn.close()
    return str([r[0] for r in rows])

@mcp.tool()
def describe_table(table_name: str) -> str:
    """Show the column names and types for a given table."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(f"PRAGMA table_info({table_name});").fetchall()
    conn.close()
    return str([{"name": r[1], "type": r[2]} for r in rows])

async def homepage(request):
    html = """
    <html>
      <head><title>Medical Equipment MCP Server</title></head>
      <body style="font-family: sans-serif; max-width: 600px; margin: 60px auto;">
        <h1>🏥 Medical Equipment MCP Server</h1>
        <p>Status: <strong style="color: green;">Running</strong></p>
        <p>This server exposes MCP tools over SSE for querying a medical equipment database.</p>
        <ul>
          <li><code>list_tables</code> — list all tables</li>
          <li><code>describe_table</code> — show a table's columns</li>
          <li><code>run_query</code> — run a read-only SELECT query</li>
        </ul>
        <p>MCP SSE endpoint: <code>/sse</code></p>
      </body>
    </html>
    """
    return HTMLResponse(html)

if __name__ == "__main__":
    # Build the MCP SSE app, then add our homepage route alongside it
    sse_app = mcp.sse_app()
    sse_app.routes.insert(0, Route("/", homepage))
    uvicorn.run(sse_app, host="0.0.0.0", port=PORT)
