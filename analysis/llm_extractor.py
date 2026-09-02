"""
LLM Extractor

Uses Google Gemini (free tier) to extract structured insights
from user review text. Handles rate limiting, JSON validation,
and graceful error recovery.
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from config.settings import GEMINI_API_KEY, LLM_MODEL, LLM_RPM_LIMIT


class LLMExtractor:
    """Extracts structured insights from text using Gemini free tier."""

    _quota_exhausted = False

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)
        self.prompt_template = self._load_prompt()
        self.request_count = 0
        self.last_request_time = 0.0
        self.rpm_limit = LLM_RPM_LIMIT

    @property
    def quota_exhausted(self) -> bool:
        return LLMExtractor._quota_exhausted

    @quota_exhausted.setter
    def quota_exhausted(self, val: bool):
        LLMExtractor._quota_exhausted = val

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent / "prompts" / "extraction_prompt.txt"
        return prompt_path.read_text()

    def _rate_limit(self):
        """Enforce free tier rate limits (15 RPM by default)."""
        if LLMExtractor._quota_exhausted:
            return
        self.request_count += 1
        elapsed = time.time() - self.last_request_time
        min_interval = 60.0 / self.rpm_limit
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _parse_retry_delay(self, error_str: str) -> float:
        """Extract retry delay from Gemini 429 error message, capped at 15s."""
        # Look for "retry in X.XXs" pattern
        match = re.search(r'retry in (\d+\.?\d*)s', error_str, re.IGNORECASE)
        if match:
            delay = float(match.group(1)) + 0.5
            return min(delay, 15.0)
        # Look for retry_delay { seconds: N }
        match = re.search(r'seconds:\s*(\d+)', error_str)
        if match:
            delay = float(match.group(1)) + 0.5
            return min(delay, 15.0)
        return 5.0  # Default fallback

    def _clean_json_response(self, text: str) -> str:
        """Strip markdown code fences if present."""
        text = text.strip()
        # Remove ```json ... ``` wrappers
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return text.strip()

    def extract(self, text: str, max_retries: int = 1) -> Dict[str, Any]:
        """Extract structured insights from a single text segment."""
        if self.quota_exhausted:
            from .heuristic_extractor import HeuristicExtractor
            heuristic = HeuristicExtractor()
            ext = heuristic.extract(text)
            return {
                "extraction": ext,
                "llm_model": f"{LLM_MODEL}+heuristic_fallback",
                "raw_response": json.dumps(ext),
                "status": "success",
            }

        self._rate_limit()
        prompt = self.prompt_template.replace("{user_text}", text)
        raw_text = None

        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                    )
                )

                raw_text = response.text
                cleaned = self._clean_json_response(raw_text)
                result = json.loads(cleaned)

                # Normalize uncertainty_type to always be a list
                if isinstance(result.get("uncertainty_type"), str):
                    result["uncertainty_type"] = [result["uncertainty_type"]]

                return {
                    "extraction": result,
                    "llm_model": LLM_MODEL,
                    "raw_response": raw_text,
                    "status": "success",
                }

            except json.JSONDecodeError:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {
                    "extraction": None,
                    "llm_model": LLM_MODEL,
                    "raw_response": raw_text,
                    "status": "json_parse_error",
                }

            except Exception as e:
                error_str = str(e)
                # Rate limit / Resource exhausted — fallback to heuristic extractor
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    self.quota_exhausted = True
                    from .heuristic_extractor import HeuristicExtractor
                    heuristic = HeuristicExtractor()
                    ext = heuristic.extract(text)
                    return {
                        "extraction": ext,
                        "llm_model": f"{LLM_MODEL}+heuristic_fallback",
                        "raw_response": json.dumps(ext),
                        "status": "success",
                    }
                # Safety filter — skip this text
                if "SAFETY" in error_str.upper() or "blocked" in error_str.lower():
                    return {
                        "extraction": None,
                        "llm_model": LLM_MODEL,
                        "raw_response": None,
                        "status": "safety_filtered",
                    }
                # Server errors — retry with backoff
                if "500" in error_str or "503" in error_str:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** (attempt + 1))
                        continue
                
                # General error fallback
                from .heuristic_extractor import HeuristicExtractor
                heuristic = HeuristicExtractor()
                ext = heuristic.extract(text)
                return {
                    "extraction": ext,
                    "llm_model": f"{LLM_MODEL}+heuristic_fallback",
                    "raw_response": json.dumps(ext),
                    "status": "success",
                }

        from .heuristic_extractor import HeuristicExtractor
        heuristic = HeuristicExtractor()
        ext = heuristic.extract(text)
        return {
            "extraction": ext,
            "llm_model": f"{LLM_MODEL}+heuristic_fallback",
            "raw_response": json.dumps(ext),
            "status": "success",
        }

    def extract_batch(self, texts: List[str], show_progress: bool = True) -> List[Dict[str, Any]]:
        """Extract from multiple texts with progress tracking."""
        from tqdm import tqdm
        results = []
        iterator = tqdm(texts, desc="LLM Extraction") if show_progress else texts

        for text in iterator:
            result = self.extract(text)
            results.append(result)

        return results
