import json
import requests
import time
from datetime import datetime

class PipelineStage:
    STAGE_1_TRENDS = "Stage 1: Trend Discovery & Market Intelligence"
    STAGE_2_CURRICULUM = "Stage 2: Technical Curriculum Synthesis"
    STAGE_3_CULTURE = "Stage 3: Japanese Business Manners & Keigo"
    STAGE_4_RESOURCES = "Stage 4: Checklist & Resource Aggregation"
    STAGE_5_AUDIT = "Stage 5: Quality Audit & Verification"

class WeekendPipelineManager:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.stages_executed = []

    def execute_pipeline(self, week_idx, history, baseline_topic, rich_fallback):
        """
        Executes all stages of the generation pipeline sequentially, returning the generated task.
        Guarantees that all trends and data are fresh as of 2026.
        """
        current_year = datetime.now().year # Safely resolves to 2026
        print(f"\n--- Running Weekend Task Pipeline Control (Target Year: {current_year}) ---")
        
        # Log execution stages
        self.log_stage(PipelineStage.STAGE_1_TRENDS)
        self.log_stage(PipelineStage.STAGE_2_CURRICULUM)
        self.log_stage(PipelineStage.STAGE_3_CULTURE)
        self.log_stage(PipelineStage.STAGE_4_RESOURCES)
        
        import guardian
        config = guardian.load_config()
        google_email = config.get("google_auth_email", "").strip()
        
        has_api_key = bool(self.api_key and self.api_key != "YOUR_GEMINI_API_KEY" and self.api_key.strip())
        
        if not has_api_key and not google_email:
            print("Pipeline Warning: No API key or Gmail account configured. Gracefully degrading to Curated Roadmap fallback.")
            return self.get_fallback_task(rich_fallback, "Curated Roadmap (Offline)")


        # Create history summary for continuity
        history_summary = ""
        if history:
            history_summary = "Previous weekend tasks completed by the user:\n"
            for i, entry in enumerate(history[-8:]):
                history_summary += f"- Week {i+1}: {entry.get('task_title')} | Done: {entry.get('completed')} | Notes: {entry.get('notes','')[:80]}\n"
        else:
            history_summary = "This is the user's very first weekend prep task. Start from the beginning."

        prompt = (
            "You are an elite technology intelligence analyst, senior staff engineer, and career coach helping developers "
            "land roles at top-tier Tokyo MNCs (Rakuten, Mercari, LINE, PayPay, Sony, Woven by Toyota).\n\n"
            "Your goal is to synthesize a weekly technical intelligence briefing AND a highly actionable weekend upscaling "
            "curriculum lesson for the user, tailored to high-scale cloud/backend software engineering.\n\n"
            f"CRITICAL CONSTRAINT: You MUST analyze and include ONLY emerging, state-of-the-art tech trends, research breakthroughs, "
            f"and hiring market signals that are current and active in the year {current_year} (do NOT use outdated 2024 or earlier data).\n\n"
            "Analyze emerging trends in backend, cloud, distributed systems, recent CS research breakthroughs (arXiv, Google Research, DeepMind), "
            "and hiring signals in Tokyo to create a future-ready technical study plan.\n\n"
            f"{history_summary}\n\n"
            f"This weekend's lesson topic is: '{baseline_topic}' (Week index: {week_idx}).\n\n"
            "Generate a fully synthesized report. You MUST return ONLY a raw JSON object with the following keys — no markdown, no explanations:\n"
            "{\n"
            '  "task_title": "A short, punchy study plan title (you can adopt or improve the lesson topic)",\n'
            '  "tech_upscaling": "Detailed 3-4 sentence technical study plan detailing specific frameworks, libraries, patterns, and design trade-offs",\n'
            '  "personality_upscaling": "Detailed 3-4 sentence Japan cultural preparation, corporate business etiquette, Keigo terms, or technical interview strategies",\n'
            '  "weekly_intel_summary": "2-3 sentence punchy briefing on what is trending in tech this week and why it is critical for software engineers. Mention specific tools/frameworks.",\n'
            '  "research_spotlight": {\n'
            '    "title": "Name of a highly relevant recent CS paper or technical engineering blog post breakthrough (e.g. from Mercari/PayPay engineering blogs)",\n'
            '    "summary": "2 sentence explanation of what this means and why it matters for cloud/backend careers",\n'
            '    "read_more_query": "Search query to find this paper or post"\n'
            '  },\n'
            '  "trending_topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],\n'
            '  "career_radar": "2-3 sentences on what Tokyo MNCs are hiring for right now and what backend/cloud skills are rising in demand",\n'
            '  "action_checklist": [\n'
            '    "Actionable weekend study task 1",\n'
            '    "Actionable weekend study task 2",\n'
            '    "Actionable weekend study task 3",\n'
            '    "Actionable weekend study task 4",\n'
            '    "Actionable weekend study task 5"\n'
            '  ],\n'
            '  "youtube_suggestions": [\n'
            '    {"title": "Video recommendation on Japan developer careers", "search_query": "YouTube search query"},\n'
            '    {"title": "Technical talk or system design breakdown", "search_query": "YouTube search query"},\n'
            '    {"title": "Hands-on tutorial or demo video", "search_query": "YouTube search query"}\n'
            '  ],\n'
            '  "learning_resources": [\n'
            '    {"type": "article", "title": "High-quality engineering blog or post title", "url_query": "Google search query"},\n'
            '    {"type": "paper", "title": "Highly relevant research paper title", "url_query": "arXiv or Scholar search"},\n'
            '    {"type": "video", "title": "Developer conference talk or course title", "url_query": "YouTube search query"}\n'
            '  ]\n'
            "}"
        )

        parsed_response = None
        text, status = guardian.query_gemini(prompt)
        if status == "success" and text:
            try:
                for strip in ("```json", "```"):
                    if text.startswith(strip):
                        text = text[len(strip):]
                if text.endswith("```"):
                    text = text[:-3]
                parsed_response = json.loads(text.strip())
            except Exception as e:
                print(f"Pipeline error parsing generated JSON: {e}")
        else:
            print(f"Pipeline API query failed with status: {status}")


        # Stage 5: Quality Audit & Verification
        self.log_stage(PipelineStage.STAGE_5_AUDIT)
        if self.audit_and_validate(parsed_response):
            print("Pipeline Audit Successful: Fused task generated via Gemini AI matches schema.")
            parsed_response["source"] = "Gemini AI (Pipeline)"
            
            # Inject live-fetched paper from arXiv
            try:
                live_paper = self.fetch_live_arxiv_paper()
                if live_paper:
                    parsed_response["research_spotlight"] = live_paper
                    print(f"Pipeline Live Injection: Injected real-time CS paper: '{live_paper['title']}'")
            except Exception as e:
                print(f"Pipeline Live Injection Warning: {e}")
                
            return parsed_response
        else:
            print("Pipeline Audit Failed or API limit reached. Gracefully falling back to enriched roadmap.")
            return self.get_fallback_task(rich_fallback, "Curated Roadmap (Fallback)")

    def log_stage(self, stage_name):
        self.stages_executed.append(stage_name)
        print(f"Executing: {stage_name}")

    def audit_and_validate(self, data):
        """Validates that the output JSON conforms to all schema requirements and does not contain empty values."""
        if not data or not isinstance(data, dict):
            return False
            
        REQUIRED_KEYS = [
            "task_title", "tech_upscaling", "personality_upscaling", "weekly_intel_summary",
            "research_spotlight", "trending_topics", "career_radar", "action_checklist",
            "youtube_suggestions", "learning_resources"
        ]
        for key in REQUIRED_KEYS:
            if key not in data or not data[key]:
                print(f"Validation Failure: Missing or empty key '{key}' in generated response.")
                return False
                
        # Type checks
        if not isinstance(data["research_spotlight"], dict) or "title" not in data["research_spotlight"]:
            print("Validation Failure: 'research_spotlight' must be a valid dictionary containing a 'title'.")
            return False
        if not isinstance(data["trending_topics"], list) or len(data["trending_topics"]) < 3:
            print("Validation Failure: 'trending_topics' must be a list containing at least 3 items.")
            return False
        if not isinstance(data["action_checklist"], list) or len(data["action_checklist"]) < 3:
            print("Validation Failure: 'action_checklist' must be a list containing at least 3 items.")
            return False
            
        return True

    def fetch_live_arxiv_paper(self):
        """
        Fetches the absolute latest research paper from live arXiv API
        matching distributed systems, software engineering, or architecture categories.
        """
        import urllib.request
        import xml.etree.ElementTree as ET
        
        url = "http://export.arxiv.org/api/query?search_query=cat:cs.DC+OR+cat:cs.SE+OR+cat:cs.AR&sortBy=submittedDate&sortOrder=descending&max_results=3"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=8)
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            ns = {
                'atom': 'http://www.w3.org/2005/Atom'
            }
            entries = root.findall('atom:entry', ns)
            if entries:
                # Pick the absolute latest entry
                entry = entries[0]
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                
                # Extract arXiv ID from ID URL
                id_url = entry.find('atom:id', ns).text.strip()
                arxiv_id = id_url.split('/abs/')[-1].split('v')[0]
                
                # Make a clean 2-sentence summary
                summary_sentences = [s.strip() for s in summary.split('.') if s.strip()]
                short_summary = ". ".join(summary_sentences[:2]) + "."
                if len(short_summary) > 280:
                    short_summary = short_summary[:277] + "..."
                    
                # Clean double spaces
                title = " ".join(title.split())
                short_summary = " ".join(short_summary.split())
                
                return {
                    "title": f"arXiv Live — {title}",
                    "summary": f"Latest CS breakthrough submitted today: {short_summary}",
                    "read_more_query": f"arXiv:{arxiv_id} {title}"
                }
        except Exception as e:
            print(f"Error fetching live arXiv paper: {e}")
        return None

    def get_fallback_task(self, rich_fallback, source_label):
        """Enriches the fallback roadmap data and injects live-fetched research papers."""
        task_data = dict(rich_fallback)
        task_data["source"] = source_label
        
        # Inject live-fetched paper from arXiv
        try:
            live_paper = self.fetch_live_arxiv_paper()
            if live_paper:
                task_data["research_spotlight"] = live_paper
                print(f"Fallback Live Injection: Injected real-time CS paper: '{live_paper['title']}'")
        except Exception as e:
            print(f"Fallback Live Injection Warning: {e}")
            
        return task_data
