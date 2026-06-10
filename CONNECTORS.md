# Ailtir Connector Reference

This file documents how Ailtir interacts with external MCP connectors.

## Supported Connectors

### Notion
**Purpose:** The business brain. Holds the CRM, Bid Pipeline, Subcontractor Directory, and RFI Log.
**Required MCP Tools:** `notion-create-database`, `notion-create-pages`, `notion-search`, `notion-update-page`.
**Setup:** Run `/ailtir-notion-setup` to build the required architecture.

### Email Connector (Gmail or Microsoft 365)
**Purpose:** Reads incoming tender alerts (eTenders, OJEU) for the automated opportunity monitor.
**Required App Integration:** Gmail or Microsoft 365 Outlook.
**Setup:** Run `/enable-monitor` to configure the scheduled background task.

### SharePoint / OneDrive (Microsoft 365)
**Purpose:** The project archive. Holds heavy tender documents, drawings, and specifications.
**Required MCP Tools:** `m365-search-files`, `m365-read-file`, `m365-upload-file`.

### Google Drive
**Purpose:** Alternative to SharePoint for project archives.
**Required MCP Tools:** `gdrive-search`, `gdrive-read`, `gdrive-upload`.

## Fallback Behavior
If a connector is offline or unavailable, Ailtir will gracefully fall back to local file system operations (saving CSVs or Markdown files instead of updating databases) and will notify the user.
