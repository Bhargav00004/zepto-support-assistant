# Zepto Support Assistant

## 1. Overview

This module implements a small Zepto support assistant as a LangGraph-orchestrated RAG service with a FastAPI `/ask` endpoint.

The graded baseline runs in fully offline mock mode with `MOCK_LLM` left unset/default. This mode does not require an LLM API key or a network LLM call.

Main technologies:
- Python
- LangGraph
- FastAPI
- ChromaDB
- sentence-transformers (`all-MiniLM-L6-v2`)
- Pydantic structured output

## 2. Module Structure

```text
support_assistant/
├── main.py
├── Dockerfile
├── requirements.txt
├── README.md
├── docs/
└── chroma_db/
```

- `main.py` contains the FastAPI application, LangGraph flow, retrieval logic, mock/optional LLM logic, and structured response handling.
- `docs/` contains the support-policy corpus used by the assistant.
- `chroma_db/` contains the local ChromaDB vector index.
- `Dockerfile` provides the container configuration for running the FastAPI service.
- `requirements.txt` lists the Python dependencies.

## 3. RAG Pipeline Architecture

The pipeline follows:

```text
Support documents
       |
       v
Document ingestion / chunking
       |
       v
Sentence-Transformer embeddings
(all-MiniLM-L6-v2)
       |
       v
ChromaDB vector store
       |
       v
User query -> /ask
       |
       v
classify_intent
       |
       +-----------------------------+
       |                             |
       v                             v
policy_question                general_question
       |                             |
       v                             v
retrieve_and_answer              direct_answer
       |                             |
       +-------------+---------------+
                     |
                     v
          Structured JSON response
          answer / sources / confidence
```

### Ingestion

The support-policy documents under `docs/` form the document corpus. The documents are processed into chunks and indexed for retrieval.

### Embedding

The project uses the open-source `sentence-transformers` model `all-MiniLM-L6-v2` to generate embeddings locally.

### Retrieval

ChromaDB stores the document embeddings and performs similarity retrieval for policy-related questions. The `retrieve_and_answer` LangGraph node uses the retrieved context to ground the answer.

### Generation

The LangGraph flow contains three nodes:

1. `classify_intent` — determines whether the query is a policy question or a general question.
2. `retrieve_and_answer` — retrieves relevant support-policy context and produces a grounded response.
3. `direct_answer` — handles general questions without policy retrieval.

With `MOCK_LLM` left at its default, generation uses deterministic offline mock logic. The retrieval step still operates against the local ChromaDB index.

## 4. LangGraph Routing

The query first enters `classify_intent`.

```text
                    classify_intent
                    /                                 /                      policy_question          general_question
             |                       |
             v                       v
   retrieve_and_answer          direct_answer
```

A policy question therefore goes through retrieval before the answer is produced. A general question is handled directly.

## 5. MOCK_LLM Mode

`MOCK_LLM` is the graded baseline.

When `MOCK_LLM` is unset (the default) or enabled for mock mode:
- no LLM provider API key is required;
- no network LLM call is made;
- the response is deterministic;
- the response is returned using the required structured schema.

The optional real-LLM path is only used when `MOCK_LLM=0` is explicitly selected.

## 6. Response Schema

The `/ask` endpoint returns structured JSON containing:

```json
{
  "answer": "...",
  "sources": [],
  "confidence": 1.0
}
```

The three required fields are:
- `answer`
- `sources`
- `confidence`

## 7. Example API Call Transcripts

The following examples should be run with `MOCK_LLM` left at its default.

### Example 1 — Policy Question

Request:

```text
POST /ask
Question: What is the return policy?
```

Expected flow:

```text
classify_intent
      |
      v
policy_question
      |
      v
retrieve_and_answer
      |
      v
structured JSON response
```

**Actual JSON response:**

> Paste the exact JSON returned by your running `/ask` endpoint here.

### Example 2 — General Question

Request:

```text
POST /ask
Question: What is the capital of France?
```

Expected flow:

```text
classify_intent
      |
      v
general_question
      |
      v
direct_answer
      |
      v
structured JSON response
```

**Actual JSON response:**

> Paste the exact JSON returned by your running `/ask` endpoint here.

> Important: the two JSON responses above should be replaced with the actual outputs produced by this project in default mock mode. Do not manually invent the responses.

## 8. Running Locally

From the `support_assistant` directory:

```bash
uvicorn main:app --host 0.0.0.0 --port 7860
```

The FastAPI service exposes the `/ask` endpoint.

## 9. Docker

Build the image from the `support_assistant` directory:

```bash
docker build -t zepto-support-assistant .
```

Run the container:

```bash
docker run -p 7860:7860 zepto-support-assistant
```

The FastAPI `/ask` endpoint is then available through the mapped port.

## 10. Optional Extensions

The real-LLM path and live cloud deployment are optional extensions and are not required for the graded offline baseline.

If a real LLM or Hugging Face Space was actually attempted, document the relevant provider/usage notes or live URL here. Otherwise, no optional extension is claimed.
