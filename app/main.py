from fastapi import FastAPI, UploadFile
from app.rag_pipeline import ingest_pdf
from app.agents import smartdocs_agent
from app.schemas import AskRequest, AskResponse

app = FastAPI(title="SmartDocs AI Assistant")


@app.post("/ingest")
async def ingest(file: UploadFile):
    return await ingest_pdf(file)


@app.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest):
    result = await smartdocs_agent.ainvoke({"question": payload.question})
    return AskResponse(**result)
