"""
Seed default crews into AgentCrew (strnad/CrewAI-Studio).
Idempotent — skips rows that already exist.
Sourced from: https://github.com/crewAIInc/crewAI-examples
"""
import json
import os
import sys
from datetime import datetime, timezone

DB_URL = os.environ.get("DB_URL", "sqlite:////app/crewai.db")
TS = datetime.now(timezone.utc).isoformat()
LLM = "openai/gpt-4o"


# ── Helpers ──────────────────────────────────────────────────────────────────

def agent(id_, role, goal, backstory, tools=None):
    return {
        "id": id_, "entity_type": "agent",
        "data": json.dumps({
            "id": id_, "role": role, "goal": goal, "backstory": backstory,
            "llm_provider_model": LLM, "temperature": 0.1,
            "allow_delegation": False, "verbose": True, "cache": True,
            "max_iter": 25, "tools": tools or [], "knowledge_source_ids": [],
            "created_at": TS,
        })
    }


def task(id_, description, expected_output, agent_id, async_execution=False,
         context_sync=None, context_async=None):
    return {
        "id": id_, "entity_type": "task",
        "data": json.dumps({
            "id": id_, "description": description,
            "expected_output": expected_output,
            "agent_id": agent_id, "async_execution": async_execution,
            "context_from_sync_tasks_ids": context_sync or [],
            "context_from_async_tasks_ids": context_async or [],
            "created_at": TS,
        })
    }


def crew(id_, name, agent_ids, task_ids, process="sequential"):
    return {
        "id": id_, "entity_type": "crew",
        "data": json.dumps({
            "id": id_, "name": name,
            "agents": agent_ids, "tasks": task_ids,
            "process": process, "verbose": True,
            "memory": False, "cache": True, "max_rpm": 1000,
            "manager_llm": None, "manager_agent": None,
            "planning": False, "planning_llm": None,
            "knowledge_source_ids": [], "created_at": TS,
        })
    }


# ── Crew definitions ─────────────────────────────────────────────────────────

ENTITIES = []


def add(*rows):
    ENTITIES.extend(rows)


# ── 1. Prep for a Meeting ─────────────────────────────────────────────────────
a1, a2, a3, a4 = "A_mtg_01", "A_mtg_02", "A_mtg_03", "A_mtg_04"
t1, t2, t3, t4 = "T_mtg_01", "T_mtg_02", "T_mtg_03", "T_mtg_04"
add(
    agent(a1, "Research Specialist",
          "Research meeting participants and their companies thoroughly.",
          "Expert at finding and synthesising background information on business professionals."),
    agent(a2, "Industry Analyst",
          "Analyse industry trends relevant to the meeting topic.",
          "Deep expertise in market analysis and competitive intelligence."),
    agent(a3, "Meeting Strategy Advisor",
          "Develop effective talking points and strategic angles for the meeting.",
          "Seasoned negotiator and business strategist with boardroom experience."),
    agent(a4, "Briefing Coordinator",
          "Compile all research into a concise, actionable briefing document.",
          "Expert at distilling complex information into executive-ready summaries."),
    task(t1, "Research each participant and their company. Summarise recent news, roles, achievements and background.",
         "Structured participant profiles with key facts and talking points.", a1, async_execution=True),
    task(t2, "Analyse the relevant industry: trends, challenges, opportunities and major players.",
         "Industry overview with 3–5 key themes relevant to the meeting.", a2, async_execution=True),
    task(t3, "Develop 5–7 strategic talking points and probing questions based on the meeting objective.",
         "Talking points and questions with supporting rationale.", a3, context_async=[t1, t2]),
    task(t4, "Compile all research into a polished briefing document ready to print or share.",
         "Complete meeting briefing: participant bios, industry overview, strategy and agenda.", a4,
         context_sync=[t3]),
    crew("C_mtg_01", "Prep for a Meeting", [a1, a2, a3, a4], [t1, t2, t3, t4]),
)

# ── 2. Job Posting Creator ────────────────────────────────────────────────────
a1, a2, a3 = "A_job_01", "A_job_02", "A_job_03"
t1, t2, t3, t4, t5 = "T_job_01", "T_job_02", "T_job_03", "T_job_04", "T_job_05"
add(
    agent(a1, "Research Analyst",
          "Analyse company culture, values and selling points from available information.",
          "Expert at extracting brand voice and culture signals from websites and materials."),
    agent(a2, "Job Description Writer",
          "Craft compelling, inclusive job descriptions that attract top talent.",
          "Experienced recruiter and copywriter with a talent for engaging job posts."),
    agent(a3, "Review & Editing Specialist",
          "Ensure job postings are clear, bias-free and professionally polished.",
          "Detail-oriented editor specialising in HR communications."),
    task(t1, "Research the company culture, values, mission and key selling points.",
         "Summary of company culture, values and EVP (Employee Value Proposition).", a1),
    task(t2, "Identify skills, qualifications and responsibilities required for the role.",
         "Structured list of must-have and nice-to-have requirements.", a1, context_sync=[t1]),
    task(t3, "Analyse industry trends to position the role attractively in the market.",
         "Industry salary benchmarks and in-demand skills for this role.", a1),
    task(t4, "Draft a complete job posting: intro, responsibilities, requirements, benefits.",
         "Full job posting draft (400–600 words).", a2, context_sync=[t1, t2, t3]),
    task(t5, "Review and polish the job posting for clarity, grammar and inclusion.",
         "Final, publish-ready job posting.", a3, context_sync=[t4]),
    crew("C_job_01", "Job Posting Creator", [a1, a2, a3], [t1, t2, t3, t4, t5]),
)

# ── 3. Marketing Strategy ─────────────────────────────────────────────────────
a1, a2, a3, a4 = "A_mkt_01", "A_mkt_02", "A_mkt_03", "A_mkt_04"
t1, t2, t3, t4, t5 = "T_mkt_01", "T_mkt_02", "T_mkt_03", "T_mkt_04", "T_mkt_05"
add(
    agent(a1, "Lead Market Analyst",
          "Research the customer, their audience and competitive landscape.",
          "Senior market researcher with 15 years in consumer insights and competitive intelligence."),
    agent(a2, "Chief Marketing Strategist",
          "Synthesise research into an actionable, channel-specific marketing strategy.",
          "CMO-level strategist who has launched 50+ successful campaigns."),
    agent(a3, "Creative Content Creator",
          "Write compelling marketing copy for each campaign idea.",
          "Award-winning copywriter with expertise across digital, social and print."),
    agent(a4, "Chief Creative Director",
          "Review all outputs for quality, brand consistency and strategic alignment.",
          "Creative director who ensures every piece of content hits its mark."),
    task(t1, "Gather competitive intelligence, audience demographics and market positioning data.",
         "Market research report: competitors, demographics, positioning.", a1),
    task(t2, "Define project goals, target persona and core brand message.",
         "Project brief: goals, target persona, key messages, USPs.", a2, context_sync=[t1]),
    task(t3, "Develop a full marketing strategy: goals, channels, KPIs and budget guidance.",
         "Marketing strategy document with channel mix and KPIs.", a2, context_sync=[t1, t2]),
    task(t4, "Generate 5 creative campaign ideas with titles, concepts and expected impact.",
         "Campaign ideation deck: 5 ideas with rationale and expected results.", a3,
         context_sync=[t2, t3]),
    task(t5, "Write marketing copy (headline, body, CTA) for each approved campaign.",
         "Ready-to-use copy for all 5 campaigns.", a3, context_sync=[t4]),
    crew("C_mkt_01", "Marketing Strategy", [a1, a2, a3, a4], [t1, t2, t3, t4, t5]),
)

# ── 4. Stock Analysis ─────────────────────────────────────────────────────────
a1, a2, a3 = "A_stk_01", "A_stk_02", "A_stk_03"
t1, t2, t3, t4 = "T_stk_01", "T_stk_02", "T_stk_03", "T_stk_04"
add(
    agent(a1, "Financial Analyst",
          "Analyse key financial metrics and compare against peers.",
          "CFA-certified analyst specialising in equity valuation and financial modelling."),
    agent(a2, "Research Analyst",
          "Gather and summarise recent news, press releases and market sentiment.",
          "Senior equity researcher with deep domain knowledge in public markets."),
    agent(a3, "Investment Advisor",
          "Synthesise all analysis into a clear investment recommendation.",
          "Portfolio manager with 20 years of buy-side experience across multiple market cycles."),
    task(t1, "Analyse financial health: P/E, EPS, revenue growth, margins, debt ratios vs peers.",
         "Financial analysis report with key metrics and peer comparison.", a1),
    task(t2, "Collect recent news, earnings call highlights, analyst ratings and sentiment.",
         "News and sentiment summary with key catalysts and risks.", a2, async_execution=True),
    task(t3, "Review latest 10-Q and 10-K SEC filings for red flags and positive signals.",
         "SEC filings analysis highlighting risks, opportunities and accounting notes.", a2,
         async_execution=True),
    task(t4, "Produce a detailed investment recommendation: Buy / Hold / Sell with rationale.",
         "Investment recommendation report with price target, thesis and risk factors.", a3,
         context_sync=[t1], context_async=[t2, t3]),
    crew("C_stk_01", "Stock Analysis", [a1, a2, a3], [t1, t2, t3, t4]),
)

# ── 5. Trip Planner ──────────────────────────────────────────────────────────
a1, a2, a3 = "A_trp_01", "A_trp_02", "A_trp_03"
t1, t2, t3 = "T_trp_01", "T_trp_02", "T_trp_03"
add(
    agent(a1, "City Selection Expert",
          "Pick the best destination based on weather, season, budget and traveller preferences.",
          "Seasoned travel consultant who has visited 80+ countries and knows what makes a trip great."),
    agent(a2, "Local City Expert",
          "Provide insider knowledge: hidden gems, cultural hotspots, customs and local costs.",
          "Former expat and travel blogger with deep local knowledge of major destinations."),
    agent(a3, "Travel Concierge",
          "Build a complete, day-by-day itinerary with budget, packing list and bookings guidance.",
          "Luxury travel planner who crafts bespoke itineraries for discerning travellers."),
    task(t1, "Compare candidate cities and select the best with a detailed rationale covering flights, weather and attractions.",
         "City selection report with top recommendation and comparison of alternatives.", a1),
    task(t2, "Compile a comprehensive city guide: attractions, hidden gems, cultural tips, local costs.",
         "City insider guide (1000+ words) with categorised recommendations.", a2,
         context_sync=[t1]),
    task(t3, "Create a complete 7-day itinerary: daily schedule, restaurant picks, hotels, weather, packing list and budget breakdown.",
         "Full 7-day travel itinerary in markdown, ready to share or print.", a3,
         context_sync=[t1, t2]),
    crew("C_trp_01", "Trip Planner (7 Days)", [a1, a2, a3], [t1, t2, t3]),
)

# ── 6. Surprise Trip ─────────────────────────────────────────────────────────
a1, a2, a3 = "A_stp_01", "A_stp_02", "A_stp_03"
t1, t2, t3 = "T_stp_01", "T_stp_02", "T_stp_03"
add(
    agent(a1, "Activity Planner",
          "Research age-appropriate activities matching the traveller's interests and energy level.",
          "Event and experience curator specialising in personalised travel."),
    agent(a2, "Restaurant Scout",
          "Find the best restaurants, cafés and scenic spots at the destination.",
          "Food critic and travel writer with knowledge of global dining scenes."),
    agent(a3, "Itinerary Compiler",
          "Combine all recommendations into a polished surprise trip itinerary.",
          "Travel logistics expert who builds seamless, delightful travel experiences."),
    task(t1, "Recommend activities per day based on the traveller's age, interests and physical ability.",
         "Activity plan: 3–4 options per day with descriptions and ratings.", a1),
    task(t2, "List top restaurants, scenic spots and fun activities with addresses and booking tips.",
         "Curated dining and sightseeing guide for the destination.", a2),
    task(t3, "Combine activities, dining and logistics into a polished day-by-day surprise itinerary.",
         "Complete surprise trip itinerary ready to hand to the traveller.", a3,
         context_sync=[t1, t2]),
    crew("C_stp_01", "Surprise Trip Planner", [a1, a2, a3], [t1, t2, t3]),
)

# ── 7. Recruitment Pipeline ───────────────────────────────────────────────────
a1, a2, a3, a4 = "A_rec_01", "A_rec_02", "A_rec_03", "A_rec_04"
t1, t2, t3, t4 = "T_rec_01", "T_rec_02", "T_rec_03", "T_rec_04"
add(
    agent(a1, "Candidate Researcher",
          "Find potential candidates matching the role requirements from online sources.",
          "Talent sourcer with deep expertise in Boolean search and LinkedIn recruiting."),
    agent(a2, "Candidate Scorer",
          "Score and rank candidates against defined criteria.",
          "Analytical recruiter who uses structured scoring to reduce hiring bias."),
    agent(a3, "Outreach Strategist",
          "Craft personalised outreach messages for top candidates.",
          "Recruitment marketer skilled at writing compelling, response-driving outreach."),
    agent(a4, "Reporting Specialist",
          "Compile a structured recruitment report for hiring managers.",
          "TA analyst who produces clear, data-driven recruitment summaries."),
    task(t1, "Find 10 candidate profiles matching the job requirements. Include name, current role, company and key skills.",
         "List of 10 candidates with profiles and estimated contact info.", a1),
    task(t2, "Score each candidate 1–10 against skills, experience and culture fit. Rank them.",
         "Scored and ranked candidate list with justification for each score.", a2,
         context_sync=[t1]),
    task(t3, "Create personalised outreach templates for the top 5 candidates.",
         "5 outreach emails tailored to each candidate's background.", a3, context_sync=[t2]),
    task(t4, "Produce a final recruitment report: top candidates, scores, outreach plan and recommended next steps.",
         "Hiring manager report in markdown with ranked shortlist and next steps.", a4,
         context_sync=[t1, t2, t3]),
    crew("C_rec_01", "Recruitment Pipeline", [a1, a2, a3, a4], [t1, t2, t3, t4]),
)

# ── 8. Instagram Campaign ─────────────────────────────────────────────────────
a1, a2, a3, a4, a5 = "A_ig_01", "A_ig_02", "A_ig_03", "A_ig_04", "A_ig_05"
t1, t2, t3, t4, t5, t6 = "T_ig_01", "T_ig_02", "T_ig_03", "T_ig_04", "T_ig_05", "T_ig_06"
add(
    agent(a1, "Lead Market Analyst",
          "Analyse the product and competitive landscape for Instagram positioning.",
          "Digital marketing analyst specialising in social media and consumer brands."),
    agent(a2, "Chief Marketing Strategist",
          "Develop a campaign direction and creative strategy.",
          "Brand strategist who has launched viral social campaigns for global brands."),
    agent(a3, "Creative Content Creator",
          "Write punchy, on-brand Instagram ad copy.",
          "Social media copywriter with a knack for thumb-stopping content."),
    agent(a4, "Senior Photographer Advisor",
          "Describe compelling photograph concepts for the campaign.",
          "Commercial photographer and art director with Instagram-native aesthetic sense."),
    agent(a5, "Chief Creative Director",
          "Review and approve final copy and creative concepts.",
          "ECD who ensures every creative output is distinctive and on-brand."),
    task(t1, "Analyse the product: features, benefits, target audience and market appeal.",
         "Product analysis brief with key selling points and audience profile.", a1),
    task(t2, "Identify top 3 competitors and compare their Instagram positioning.",
         "Competitive analysis with differentiators and white space opportunities.", a1,
         async_execution=True),
    task(t3, "Develop campaign strategy: creative direction, tone, hashtag strategy and content pillars.",
         "Campaign strategy brief with creative direction and content pillars.", a2,
         context_sync=[t1, t2]),
    task(t4, "Write 3 Instagram ad copy options: hook, body and CTA. Max 150 words each.",
         "3 Instagram ad copy variants ready for A/B testing.", a3, context_sync=[t3]),
    task(t5, "Describe 3 photograph concepts: shot type, lighting, props, model direction.",
         "3 photography briefs with detailed visual direction.", a4, context_sync=[t3]),
    task(t6, "Review all copy and photography concepts. Select and refine the best combination.",
         "Final approved Instagram campaign: 1 copy variant + 1 photo concept with notes.", a5,
         context_sync=[t4, t5]),
    crew("C_ig_01", "Instagram Campaign Creator", [a1, a2, a3, a4, a5], [t1, t2, t3, t4, t5, t6]),
)

# ── 9. Game Builder ───────────────────────────────────────────────────────────
a1, a2, a3 = "A_gm_01", "A_gm_02", "A_gm_03"
t1, t2, t3 = "T_gm_01", "T_gm_02", "T_gm_03"
add(
    agent(a1, "Senior Software Engineer",
          "Write clean, functional Python game code from a description.",
          "Python developer with 10 years building games and interactive applications."),
    agent(a2, "QA Engineer",
          "Review code for syntax errors, logic issues and missing imports.",
          "Software tester specialising in Python code review and static analysis."),
    agent(a3, "Chief QA Engineer",
          "Evaluate whether the final code fulfils the stated game requirements.",
          "Lead QA architect who signs off on production-ready code."),
    task(t1, "Write complete, runnable Python code for the described game. Include all imports.",
         "Full Python game source code in a single file.", a1),
    task(t2, "Review the code for errors, missing imports, logic bugs and security issues.",
         "Code review report with identified issues and fixes applied.", a2, context_sync=[t1]),
    task(t3, "Confirm the code meets the game requirements and is ready to run.",
         "Final approved game code with QA sign-off notes.", a3, context_sync=[t2]),
    crew("C_gm_01", "Python Game Builder", [a1, a2, a3], [t1, t2, t3]),
)

# ── 10. CV to Job Matcher ──────────────────────────────────────────────────────
a1, a2, a3 = "A_cv_01", "A_cv_02", "A_cv_03"
t1, t2 = "T_cv_01", "T_cv_02"
add(
    agent(a1, "CV Analyst",
          "Extract and structure skills, experience and achievements from a CV.",
          "HR specialist who can parse any resume format into structured data."),
    agent(a2, "Job Opportunities Parser",
          "Extract job requirements from a list of open positions.",
          "Recruitment analyst who understands what employers really need."),
    agent(a3, "Match Maker",
          "Match candidate profile to job openings and rank by fit.",
          "Talent matching expert who quantifies fit with evidence-based scoring."),
    task(t1, "Parse the CV into a structured profile: summary, skills, work history, education.",
         "Structured candidate profile JSON with categorised skills and experience.", a1),
    task(t2, "Compare the candidate profile to all job openings. Score each match 1–10 and rank.",
         "Ranked list of best-matching roles with score and matching rationale.", a3,
         context_sync=[t1]),
    crew("C_cv_01", "CV to Job Matcher", [a1, a2, a3], [t1, t2]),
)

# ── 11. Landing Page Generator ────────────────────────────────────────────────
a1, a2, a3, a4 = "A_lp_01", "A_lp_02", "A_lp_03", "A_lp_04"
t1, t2, t3, t4 = "T_lp_01", "T_lp_02", "T_lp_03", "T_lp_04"
add(
    agent(a1, "Idea Analyst",
          "Expand an idea into a validated brief with value propositions and pain points.",
          "Product strategist who turns rough ideas into clear, compelling propositions."),
    agent(a2, "Communications Strategist",
          "Apply the Golden Circle (Why/How/What) framework to the messaging.",
          "Brand messaging expert who crafts narratives that resonate and convert."),
    agent(a3, "React Engineer",
          "Write the landing page component code in React + Tailwind.",
          "Senior frontend engineer specialising in high-converting landing pages."),
    agent(a4, "Content Editor",
          "Review and polish all landing page copy for clarity and conversion.",
          "CRO-focused editor who optimises every word for maximum impact."),
    task(t1, "Expand the idea: USPs, target market, pain points solved and differentiation.",
         "Validated idea brief with USPs and target audience definition.", a1),
    task(t2, "Develop Why/How/What messaging and a hero headline with supporting copy.",
         "Golden Circle messaging framework with hero headline and sub-copy.", a2,
         context_sync=[t1]),
    task(t3, "Write React + Tailwind components for the landing page (Hero, Features, CTA, Footer).",
         "Complete landing page source code in React/Tailwind.", a3, context_sync=[t1, t2]),
    task(t4, "Review all copy and code for quality, clarity, grammar and conversion best practices.",
         "Final landing page with polished copy and clean code.", a4, context_sync=[t3]),
    crew("C_lp_01", "Landing Page Generator", [a1, a2, a3, a4], [t1, t2, t3, t4]),
)

# ── 12. Screenplay Writer ─────────────────────────────────────────────────────
a1, a2, a3 = "A_sp_01", "A_sp_02", "A_sp_03"
t1, t2, t3 = "T_sp_01", "T_sp_02", "T_sp_03"
add(
    agent(a1, "Story Developer",
          "Develop the story premise, characters, three-act structure and scene breakdown.",
          "Story consultant with credits on award-winning films and TV series."),
    agent(a2, "Screenplay Writer",
          "Write the full screenplay in standard format.",
          "WGA-trained screenwriter who writes compelling dialogue and vivid action lines."),
    agent(a3, "Script Editor",
          "Review and polish the screenplay for pacing, dialogue and structure.",
          "Development executive who has polished scripts for major studios."),
    task(t1, "Develop the story: logline, characters, three-act structure and key scenes.",
         "Story bible: logline, character profiles, act breakdown and scene list.", a1),
    task(t2, "Write the full screenplay in standard format (Fade In to Fade Out).",
         "Complete screenplay in standard format.", a2, context_sync=[t1]),
    task(t3, "Review the screenplay for pacing, dialogue authenticity and structural issues.",
         "Polished, production-ready screenplay with editor's notes.", a3, context_sync=[t2]),
    crew("C_sp_01", "Screenplay Writer", [a1, a2, a3], [t1, t2, t3]),
)

# ── 13. Markdown Validator ────────────────────────────────────────────────────
a1 = "A_md_01"
t1 = "T_md_01"
add(
    agent(a1, "Documentation QA Specialist",
          "Validate markdown files against linting rules and produce actionable fixes.",
          "Technical writer who maintains documentation quality across large codebases."),
    task(t1, "Run markdown linting on the provided file path and list all issues with line numbers and fixes.",
         "Actionable markdown fix list: issue, line number and recommended correction.", a1),
    crew("C_md_01", "Markdown Validator", [a1], [t1]),
)

# ── 14. Content Creator (SEO Blog) ───────────────────────────────────────────
a1, a2, a3 = "A_blog_01", "A_blog_02", "A_blog_03"
t1, t2, t3 = "T_blog_01", "T_blog_02", "T_blog_03"
add(
    agent(a1, "SEO Research Specialist",
          "Research the topic, identify target keywords and analyse top-ranking content.",
          "SEO strategist with 10 years of experience in organic search and content strategy."),
    agent(a2, "Content Writer",
          "Write a comprehensive, SEO-optimised blog post on the given topic.",
          "Professional content writer who produces engaging, authoritative long-form content."),
    agent(a3, "Content Editor",
          "Review and polish the article for quality, accuracy and SEO best practices.",
          "Senior editor who ensures every piece of content meets publication standards."),
    task(t1, "Research the topic: target keyword, secondary keywords, search intent and top 5 competing articles.",
         "SEO research brief with keyword targets, search intent and content gaps.", a1),
    task(t2, "Write a 1500-word SEO-optimised blog post with H2s, H3s, intro, body and conclusion.",
         "Complete blog post draft with proper heading structure and keyword placement.", a2,
         context_sync=[t1]),
    task(t3, "Review the article for factual accuracy, readability, SEO and brand voice.",
         "Final polished article ready to publish.", a3, context_sync=[t2]),
    crew("C_blog_01", "SEO Blog Writer", [a1, a2, a3], [t1, t2, t3]),
)


# ── DB seeding ────────────────────────────────────────────────────────────────

def seed():
    import sqlalchemy as sa

    engine = sa.create_engine(DB_URL)

    with engine.connect() as conn:
        # Ensure table exists (mirrors strnad's db_utils.py init)
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS entities (
                id          TEXT PRIMARY KEY,
                entity_type TEXT,
                data        TEXT
            )
        """))
        conn.commit()

        existing = {row[0] for row in conn.execute(sa.text("SELECT id FROM entities"))}
        inserted = 0

        for row in ENTITIES:
            if row["id"] in existing:
                continue
            conn.execute(
                sa.text("INSERT INTO entities (id, entity_type, data) VALUES (:id, :entity_type, :data)"),
                row,
            )
            inserted += 1

        conn.commit()

    total_crews = sum(1 for e in ENTITIES if e["entity_type"] == "crew")
    print(f"[seed_crews] {inserted} entities inserted ({total_crews} crews). "
          f"{len(existing)} already existed — skipped.")


if __name__ == "__main__":
    try:
        seed()
    except Exception as exc:
        print(f"[seed_crews] WARNING: seeding failed — {exc}", file=sys.stderr)
        sys.exit(0)   # Don't block app startup on seed failure
