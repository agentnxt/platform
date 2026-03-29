"""
AutonomyX Agentic Content Management Service
Agents: Research, Write, Repurpose, Publish
"""
import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="AutonomyX Content Agent", version="0.1.0")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4000")
PORT = int(os.getenv("AGENT_PORT", "8100"))


# ── Models ──────────────────────────────────────────────────────
class ContentRequest(BaseModel):
    topic: str
    content_type: str = "blog_post"  # blog_post, social_post, email, ad_copy
    brand_name: Optional[str] = None
    tone: str = "professional"  # professional, casual, technical, friendly
    length: str = "medium"  # short, medium, long
    target_audience: Optional[str] = None
    model: str = "qwen2.5:7b"


class RepurposeRequest(BaseModel):
    content: str
    target_formats: list[str] = ["twitter", "linkedin", "instagram"]
    brand_name: Optional[str] = None
    model: str = "phi3.5:latest"


class BrandMemoryRequest(BaseModel):
    brand_name: str
    content: str  # brand guidelines, style guide, past content
    content_type: str = "guidelines"  # guidelines, past_content, voice_sample


class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"  # quick, standard, deep
    model: str = "qwen2.5:7b"


# ── LLM Helper ─────────────────────────────────────────────────
async def generate(prompt: str, model: str = "qwen2.5:7b", system: str = "") -> str:
    """Generate text using Ollama via LiteLLM or direct."""
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            # Try LiteLLM first
            resp = await client.post(f"{LITELLM_URL}/chat/completions", json={
                "model": f"ollama/{model}",
                "messages": [
                    {"role": "system", "content": system} if system else None,
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4096
            })
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass

        # Fallback to Ollama direct
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 4096}
        })
        resp.raise_for_status()
        return resp.json()["response"]


# ── Vector DB Helper ───────────────────────────────────────────
async def store_brand_memory(brand_name: str, text: str, metadata: dict):
    """Store brand content in Qdrant for RAG."""
    async with httpx.AsyncClient(timeout=30) as client:
        # Create collection if not exists
        try:
            await client.put(f"{QDRANT_URL}/collections/{brand_name}", json={
                "vectors": {"size": 384, "distance": "Cosine"}
            })
        except Exception:
            pass

        # Generate embedding via Ollama
        emb_resp = await client.post(f"{OLLAMA_URL}/api/embed", json={
            "model": "nomic-embed-text",
            "input": text[:2000]
        })
        if emb_resp.status_code != 200:
            return {"status": "embedding_failed"}

        embedding = emb_resp.json()["embeddings"][0]

        # Store in Qdrant
        import uuid
        point_id = str(uuid.uuid4())
        await client.put(f"{QDRANT_URL}/collections/{brand_name}/points", json={
            "points": [{
                "id": point_id,
                "vector": embedding,
                "payload": {"text": text, **metadata}
            }]
        })
        return {"status": "stored", "id": point_id}


async def search_brand_memory(brand_name: str, query: str, limit: int = 3) -> list:
    """Search brand memory for relevant context."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            emb_resp = await client.post(f"{OLLAMA_URL}/api/embed", json={
                "model": "nomic-embed-text",
                "input": query
            })
            if emb_resp.status_code != 200:
                return []

            embedding = emb_resp.json()["embeddings"][0]

            search_resp = await client.post(
                f"{QDRANT_URL}/collections/{brand_name}/points/search",
                json={"vector": embedding, "limit": limit, "with_payload": True}
            )
            if search_resp.status_code == 200:
                return [hit["payload"]["text"] for hit in search_resp.json().get("result", [])]
        except Exception:
            pass
        return []


# ── Agents ─────────────────────────────────────────────────────

@app.post("/agent/research")
async def research_agent(req: ResearchRequest):
    """Research a topic and return structured findings."""
    prompt = f"""Research the topic: "{req.topic}"

Provide:
1. Key trends and developments
2. Target audience insights
3. Content angles (3-5 unique angles)
4. Keywords and phrases to use
5. Competitor content gaps

Format as structured JSON."""

    result = await generate(prompt, req.model, system="You are a content research expert. Return structured JSON.")
    return {"topic": req.topic, "research": result}


@app.post("/agent/write")
async def writer_agent(req: ContentRequest):
    """Write content based on topic, type, and brand guidelines."""
    # Get brand context from memory
    brand_context = ""
    if req.brand_name:
        memories = await search_brand_memory(req.brand_name, req.topic)
        if memories:
            brand_context = f"\n\nBrand Guidelines & Context:\n" + "\n".join(memories)

    length_guide = {"short": "200-300 words", "medium": "500-800 words", "long": "1200-2000 words"}

    type_prompts = {
        "blog_post": f"Write a {length_guide[req.length]} blog post",
        "social_post": "Write a social media post (280 chars for Twitter, longer for LinkedIn)",
        "email": f"Write a marketing email ({length_guide[req.length]})",
        "ad_copy": "Write compelling ad copy (headline + body + CTA)",
    }

    prompt = f"""{type_prompts.get(req.content_type, "Write content")} about: "{req.topic}"

Tone: {req.tone}
Target audience: {req.target_audience or "general"}
{brand_context}

Make it engaging, SEO-friendly, and actionable."""

    system = f"You are an expert content writer. Write in a {req.tone} tone."
    result = await generate(prompt, req.model, system=system)

    return {
        "topic": req.topic,
        "content_type": req.content_type,
        "content": result,
        "model": req.model
    }


@app.post("/agent/repurpose")
async def repurpose_agent(req: RepurposeRequest):
    """Repurpose content into multiple formats."""
    results = {}
    for fmt in req.target_formats:
        format_prompts = {
            "twitter": "Rewrite as a Twitter/X post (max 280 chars). Include relevant hashtags.",
            "linkedin": "Rewrite as a LinkedIn post (300-500 words). Professional, insightful tone. Include a hook.",
            "instagram": "Rewrite as an Instagram caption. Engaging, include emojis and hashtags.",
            "email_subject": "Write 3 email subject line variations. Short, compelling, high open-rate.",
            "facebook": "Rewrite as a Facebook post. Conversational, shareable.",
            "newsletter": "Rewrite as a newsletter section (200-300 words). Informative, scannable.",
            "ad_headline": "Write 5 ad headline variations. Short, punchy, action-oriented.",
        }

        prompt = f"""{format_prompts.get(fmt, f"Rewrite for {fmt}")}

Original content:
{req.content[:3000]}"""

        result = await generate(prompt, req.model, system="You are a content repurposing expert.")
        results[fmt] = result

    return {"formats": results}


@app.post("/brand/memory")
async def add_brand_memory(req: BrandMemoryRequest):
    """Store brand guidelines, voice samples, or past content for RAG."""
    result = await store_brand_memory(
        brand_name=req.brand_name,
        text=req.content,
        metadata={"type": req.content_type, "brand": req.brand_name}
    )
    return result


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "autonomyx-content-agent"}


@app.get("/models")
async def list_models():
    """List available models."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
    return {"models": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
