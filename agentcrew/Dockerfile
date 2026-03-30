FROM python:3.12.10-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && rm -rf /var/lib/apt/lists/*

# Clone strnad's CrewAI-Studio (main — no stable release exists)
RUN git clone --depth 1 https://github.com/strnad/CrewAI-Studio.git /app

WORKDIR /app

# Install all deps (includes crewai==1.5.0 + crewai-tools==1.5.0)
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytrends httpx amadeus

# Our additions
COPY seed_crews.py /app/seed_crews.py
COPY searxng_tool.py /app/searxng_tool.py
COPY trends_tool.py /app/trends_tool.py
COPY amadeus_tool.py /app/amadeus_tool.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8501

ENTRYPOINT ["/entrypoint.sh"]
