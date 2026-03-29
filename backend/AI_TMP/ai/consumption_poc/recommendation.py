import difflib
import json
import os

import pandas as pd

from consumption_poc.config import DEFAULT_GEMINI_MODEL, get_env


class AIConsumptionEngine:
    def __init__(self, personas, cards):
        self.personas = personas
        self.cards = cards

        config_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "raw", "store_mapping.json"
        )
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.keyword_map = json.load(f)
        else:
            self.keyword_map = {}

        try:
            gemini_key = get_env("GEMINI_API_KEY")
            if gemini_key:
                from google import genai

                self.llm_client = genai.Client(api_key=gemini_key)
            else:
                self.llm_client = None
        except Exception:
            self.llm_client = None

    @staticmethod
    def _normalize_token(value: str) -> str:
        return (
            str(value or "")
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
            .replace("/", "_")
        )

    def _get_llm_category(self, store_name: str) -> str:
        if not self.llm_client:
            return "ETC"
        try:
            categories_desc = ", ".join([f"{k}({v[0]})" for k, v in self.keyword_map.items()])
            prompt = (
                "Given merchant text, choose one category code from P01..P13 only. "
                "If uncertain, return ETC.\n\n"
                f"Categories: {categories_desc}\n"
                f"Merchant: {store_name}\n"
                "Answer format: one code only."
            )
            response = self.llm_client.models.generate_content(
                model=DEFAULT_GEMINI_MODEL,
                contents=prompt,
            )
            result = (getattr(response, "text", "") or "").strip()
            if result in self.keyword_map or result == "ETC":
                return result
        except Exception:
            pass
        return "ETC"

    def match_type(self, row) -> str:
        store_name = str(row.get("storeName", "")).strip()
        subcategory = self._normalize_token(row.get("subcategory", ""))
        category = self._normalize_token(row.get("category", ""))
        store_name_norm = store_name.lower()
        context_text = " ".join(
            [
                str(row.get("storeName", "")),
                str(row.get("category", "")),
                str(row.get("subcategory", "")),
            ]
        ).lower()

        sub_to_p = {
            "delivery": "P01",
            "convenience_store": "P02",
            "fastfood": "P01",
            "ott": "P04",
            "music": "P04",
            "taxi": "P05",
            "health_beauty": "P06",
            "cafe": "P07",
            "fashion": "P08",
            "ecommerce": "P08",
            "book": "P09",
            "course": "P09",
            "academy": "P09",
            "groceries": "P10",
            "home": "P10",
            "living": "P06",
            "flight": "P11",
            "hotel": "P11",
            "package": "P11",
            "luxury": "P12",
            "department_store": "P12",
            "movie": "P13",
            "hobby": "P13",
            "gaming": "P13",
        }
        if subcategory in sub_to_p:
            return sub_to_p[subcategory]

        category_to_p = {
            "food": "P01",
            "transport": "P05",
            "shopping": "P08",
            "subscription": "P04",
            "education": "P09",
            "health": "P06",
            "travel": "P11",
            "leisure": "P13",
            "convenience_store": "P02",
            "convenience": "P02",
            "mart": "P10",
            "cafe": "P07",
            "dessert": "P07",
            "medical": "P06",
            "wellness": "P06",
            "culture": "P13",
            "식사_음식": "P01",
            "편의점_마트": "P02",
            "카페_디저트": "P07",
            "의료_건강": "P06",
            "문화_여가": "P13",
        }
        if category in category_to_p:
            return category_to_p[category]

        for type_id, keywords in self.keyword_map.items():
            if any(str(kw).lower() in context_text for kw in keywords):
                return type_id

        for type_id, keywords in self.keyword_map.items():
            if any(str(kw).lower() in store_name_norm for kw in keywords):
                return type_id

        lowered_to_type = {
            str(kw).lower(): type_id
            for type_id, keywords in self.keyword_map.items()
            for kw in keywords
        }
        matches = difflib.get_close_matches(store_name_norm, lowered_to_type.keys(), n=1, cutoff=0.6)
        if matches:
            return lowered_to_type[matches[0]]

        return self._get_llm_category(store_name)

    def preprocess(self, raw_data):
        df = pd.DataFrame(raw_data)
        df["type_id"] = df.apply(self.match_type, axis=1)
        df["amount"] = pd.to_numeric(df["amount"])
        return df

    def get_persona_score(self, df):
        stats = (
            df.groupby("type_id")
            .agg(total_amount=("amount", "sum"), count=("amount", "count"))
            .to_dict("index")
        )

        scored_personas = []
        for persona in self.personas:
            type_id = persona["type_id"]
            stat = stats.get(type_id, {"total_amount": 0, "count": 0})
            score = (stat["total_amount"] * 0.7) + (stat["count"] * 10000 * 0.3)
            if score > 0:
                persona_name = persona.get("nickname") or persona.get("name") or type_id
                scored_personas.append(
                    {
                        **persona,
                        "name": persona_name,
                        "nickname": persona.get("nickname", persona_name),
                        **stat,
                        "score": int(score),
                    }
                )

        scored_personas.sort(key=lambda x: x["score"], reverse=True)
        return (scored_personas[0] if scored_personas else None), stats

    def simulate_benefits(self, stats, total_spend):
        simulation_results = []

        for card in self.cards:
            savings = 0
            structured_benefits = card.get("benefits", {}).get("structured", [])
            for benefit in structured_benefits:
                target_type = benefit.get("target_type")
                rate = benefit.get("rate", 0.0)
                if target_type in stats:
                    savings += stats[target_type]["total_amount"] * rate

            benefits = card.get("benefits", {})
            simulation_results.append(
                {
                    "card_id": card.get("card_id"),
                    "name": card.get("name"),
                    "main_text": benefits.get("main_text", ""),
                    "sub_text": benefits.get("sub_text", []),
                    "structured_benefits": structured_benefits,
                    "estimated_savings": int(savings),
                    "picking_rate": round((savings / total_spend) * 100, 2) if total_spend > 0 else 0,
                    "comment": card.get("recommend_comment"),
                }
            )

        simulation_results.sort(key=lambda x: x["estimated_savings"], reverse=True)
        return simulation_results

    def run(self, raw_data):
        df = self.preprocess(raw_data)
        total_spend = df["amount"].sum()
        user_persona, stats = self.get_persona_score(df)
        recommendations = self.simulate_benefits(stats, total_spend)
        best_card = recommendations[0] if recommendations and recommendations[0]["estimated_savings"] > 0 else None

        return {
            "user_persona": user_persona,
            "best_card": best_card,
            "all_cards": recommendations,
            "total_spend": int(total_spend),
            "type_spend_stats": {k: int(v.get("total_amount", 0)) for k, v in stats.items()},
        }
