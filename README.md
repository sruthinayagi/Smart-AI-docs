smartdocs-ai/
│
├── app/
│   ├── main.py                # FastAPI server
│   ├── agents.py              # LangGraph agent
│   ├── tools.py               # Tool functions
│   ├── rag_pipeline.py        # Ingest + retrieval
│   ├── schemas.py             # Request/response models
│   ├── evaluator.py           # Quality checks
│   ├── observability.py       # Metrics + logs
│   └── config.py              # Env configs
│
├── data/
│   └── pdfs/                  # Uploaded documents
│
├── vectorstore/
│   └── chroma/                # Chroma DB files
│
└── requirements.txt