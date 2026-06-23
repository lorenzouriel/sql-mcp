<div class="hero">
  <h1>sql-mcp</h1>
  <p>One MCP server to rule them all — connect Claude and any MCP-compatible framework to MSSQL, PostgreSQL, MySQL, MariaDB, SQLite, MongoDB, Databricks, and Microsoft Fabric.</p>
  <div class="badges">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/MCP-1.2%2B-purple" alt="MCP">
    <img src="https://img.shields.io/badge/version-3.0.0-blue" alt="Version">
  </div>
  <div class="hero-buttons">
    <a href="getting-started/" class="btn-primary">Get Started</a>
    <a href="https://github.com/lorenzouriel/sql-mcp" class="btn-secondary">GitHub</a>
  </div>
</div>

## Supported Engines

<div class="engine-grid">
  <div class="engine-card">
    <div class="engine-icon">🗄️</div>
    <div class="engine-name">SQL Server</div>
    <div class="engine-lang">T-SQL</div>
  </div>
  <div class="engine-card">
    <div class="engine-icon">🐘</div>
    <div class="engine-name">PostgreSQL</div>
    <div class="engine-lang">SQL</div>
  </div>
  <div class="engine-card">
    <div class="engine-icon">🐬</div>
    <div class="engine-name">MySQL</div>
    <div class="engine-lang">SQL</div>
  </div>
  <div class="engine-card">
    <div class="engine-icon">🦭</div>
    <div class="engine-name">MariaDB</div>
    <div class="engine-lang">SQL</div>
  </div>
  <div class="engine-card">
    <div class="engine-icon">🪶</div>
    <div class="engine-name">SQLite</div>
    <div class="engine-lang">SQL</div>
  </div>
  <div class="engine-card">
    <div class="engine-icon">🍃</div>
    <div class="engine-name">MongoDB</div>
    <div class="engine-lang">MQL</div>
  </div>
  <div class="engine-card">
    <div class="engine-icon">⚡</div>
    <div class="engine-name">Databricks</div>
    <div class="engine-lang">SparkSQL</div>
  </div>
  <div class="engine-card">
    <div class="engine-icon">🧵</div>
    <div class="engine-name">Fabric</div>
    <div class="engine-lang">T-SQL / KQL</div>
  </div>
</div>

## Why sql-mcp?

<div class="feature-grid">
  <div class="feature-card">
    <h3>🔌 One Server, Eight Engines</h3>
    <p>Register up to 20 named connections across any combination of SQL and NoSQL engines in a single session.</p>
  </div>
  <div class="feature-card">
    <h3>🔒 Secure by Default</h3>
    <p>Read-only mode, per-engine banned pattern lists, multi-statement blocking, and SHA-256 audit logging on every query.</p>
  </div>
  <div class="feature-card">
    <h3>🍃 Native MQL Support</h3>
    <p>Query MongoDB with real MQL — filter dicts or aggregation pipelines — not SQL wrappers.</p>
  </div>
  <div class="feature-card">
    <h3>⚡ SparkSQL + KQL</h3>
    <p>Full Databricks SparkSQL and Microsoft Fabric KQL (Eventhouse) support alongside standard T-SQL.</p>
  </div>
  <div class="feature-card">
    <h3>📦 Lean by Default</h3>
    <p>Install only the drivers you need. MongoDB, Databricks, and Fabric adapters are soft-loaded — missing drivers don't crash the server.</p>
  </div>
  <div class="feature-card">
    <h3>📊 Observable</h3>
    <p>Prometheus metrics, structured JSON logging with sensitive data redaction, and HTTP health endpoints.</p>
  </div>
</div>

## Quick Install

```bash
# All engines
pip install "sql-mcp[all]"

# Only what you need
pip install "sql-mcp[postgres,mongodb]"
```

Then add to your Claude Desktop config and restart:

```json
{
  "mcpServers": {
    "sql-mcp": {
      "command": "sql-mcp",
      "args": ["--transport", "stdio", "--config", "/path/to/connections.json"]
    }
  }
}
```

→ [Full Quick Start](getting-started.md)
