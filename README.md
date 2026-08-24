# ai-deep-rag-agent-research


financial-agent/
├── src/
│   └── financial_agent/
│       ├── __init__.py
│       ├── state.py           # Định nghĩa State
│       ├── tools.py           # Các tool (sẽ tích hợp MCP sau)
│       ├── nodes.py           # Các node xử lý
│       ├── agents.py          # Tạo các agent con
│       ├── supervisor.py      # Xây dựng supervisor workflow
│       └── app.py             # Entry point chính
├── .env                        # API keys
├── requirements.txt
└── main.py                     # File chạy thử