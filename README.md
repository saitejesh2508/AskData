# Voice Data Analyst (Alexa+ MCP server)

A self-hosted MCP server (Streamable HTTP) that lets Alexa+ answer spoken questions about CSV data.
Each tool returns a short `speech` sentence for the assistant to say, plus structured data.

## Tools
| Tool | Example utterance |
|---|---|
| `list_datasets` | "What data do you have?" |
| `describe_dataset` | "Describe the sales dataset." |
| `top_n` | "Top three regions by revenue." |
| `trend` | "How is revenue trending?" |
| `compare` | "Compare South and North revenue." |

## Run
```bash
pip install -r requirements.txt
python server.py            # serves http://localhost:8000/mcp
```
Drop any `.csv` into `data/` and it becomes a dataset (columns containing "date" are parsed as dates).

## Try it
```bash
npx @modelcontextprotocol/inspector   # connect to http://localhost:8000/mcp (Streamable HTTP)
```
To expose it to Alexa+, deploy behind HTTPS (e.g. an EC2/App Runner service or `ngrok http 8000`) and register the `/mcp` URL.

## Config
`HOST`, `PORT`, `DATA_DIR` environment variables.

## License
MIT
