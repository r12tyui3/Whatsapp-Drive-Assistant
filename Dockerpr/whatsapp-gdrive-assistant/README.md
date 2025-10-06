# WhatsApp-Driven Google Drive Assistant

This project implements a WhatsApp-driven assistant for Google Drive operations using n8n workflow automation. It allows users to control Google Drive files and folders via WhatsApp commands.

## Commands Supported

- **LIST /FolderName**: Lists all files in the specified folder.
- **DELETE /FolderName/file.pdf**: Deletes the specified file (placeholder response).
- **MOVE /FolderName/file.pdf /Archive**: Moves a file to another folder (placeholder response).
- **SUMMARY /FolderName**: Generates an AI-powered summary of all documents in the folder (placeholder response, requires full implementation).
- **RENAME file.pdf NewFileName.pdf**: Renames the specified file (placeholder response).
- **UPLOAD /FolderName**: Uploads a file sent via WhatsApp to the specified folder (placeholder response, for uploads with attachments, additional logic needed).

## Prerequisites

- Docker and Docker Compose
- Google Cloud Console account for Google Drive API
- Twilio account for WhatsApp Business API
- Optional: OpenAI API key for AI summaries

## Setup Instructions

1. **Clone the Repository**
   ```
   git clone <your-repo-url>
   cd whatsapp-gdrive-assistant
   ```

2. **Start n8n using Docker Compose**
   ```
   docker-compose up -d
   ```
   n8n will be accessible at `http://localhost:5678` with credentials: admin / securepassword

3. **Import the Workflow**
   - Open n8n in your browser
   - Click "Workflow" > "Import from File"
   - Select the `workflow.json` file from this repository
   - The workflow includes logic for the LIST command and placeholders for others

4. **Configure Credentials**

   **Google Drive:**
   - Create a project in Google Cloud Console
   - Enable Google Drive API
   - Create OAuth 2.0 credentials (Desktop/Web application)
   - In n8n, go to Credentials > Add New > Google Drive OAuth2 API
   - Enter your Client ID and Secret
   - Authorize access to Google Drive

   **Twilio WhatsApp:**
   - Set up WhatsApp on Twilio (sandbox or production)
   - Obtain Account SID, Auth Token, and WhatsApp number
   - In n8n, go to Credentials > Add New > Twilio (SMS/WhatsApp)
   - Enter your SID and Auth Token

   **AI (for SUMMARY - Optional):**
   - Get API key from OpenAI or Claude
   - Add as Credential in n8n (e.g., OpenAI API)

5. **Configure Webhook**
   - In n8n, activate the workflow temporarily to get the webhook URL
   - Go to the Webhook node's test tab to find the URL (e.g., `https://your-n8n-instance.com/webhook/whatsapp-hook`)
   - In Twilio, set this URL as the WhatsApp webhook for incoming messages
   - For local development, use a tool like ngrok to expose port 5678: `ngrok http 5678`

6. **Test the Workflow**
   - Send a WhatsApp message with "LIST My Folder" (replace "My Folder" with an actual folder name in your Google Drive)
   - The assistant should respond with the list of files

## Extending the Workflow

The provided `workflow.json` implements basic LIST functionality. To fully support all commands:

- For DELETE, MOVE, RENAME: Add Google Drive delete/move/rename nodes after finding the file
- For SUMMARY: Add a loop to download and extract text from each document, then send to AI node for summarization
- For UPLOAD: Handle incoming media attachments from WhatsApp, download, and upload to Google Drive

Add necessary nodes and update the switch connections accordingly.

## Deployment

For production deployment:

- Use a VPS or cloud service (e.g., AWS, DigitalOcean)
- Configure environment variables for security
- Set up HTTPS with a reverse proxy (nginx/Caddy)
- Update Twilio webhook with the production URL
- Use n8n's built-in database or external PostgreSQL

## Handling API Keys

- API keys and credentials are managed in n8n's Credentials section
- For self-hosted n8n, data is stored in `./data` volume by default
- Change keys by updating credentials in n8n UI

## Limitations

- **Google Native Formats**: Optimization for Google Docs, Sheets, etc., may require additional conversion nodes for preview/summary
- **File Size**: WhatsApp has message size limits; large files cannot be uploaded through WhatsApp
- **AI Integration**: SUMMARY command needs full implementation with PDF text extraction and AI processing
- **Error Handling**: Add try-catch logic for robust error responses

## Demo

A short demo video showcasing command execution can be found in this repository (referenced as demo-video.mp4 - create and add separately).

## References

Inspired by n8n template: https://n8n.io/workflows/7663-build-a-whatsapp-assistant-with-memory-google-suite-and-multi-ai-research-and-imaging
