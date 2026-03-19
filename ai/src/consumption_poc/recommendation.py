import os
import json
import difflib
import pandas as pd
from openai import OpenAI

class AIConsumptionEngine:
    def __init__(self, personas, cards):
        self.personas = personas
        self.cards = cards
        
        # 1. 분리된 설정 파일 읽기 (store_mapping.json)
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'store_mapping.json')
        # 파일이 없을 경우를 대비한 fall-back 처리는 유지하지만, 기본적으로 분리된 파일을 사용합니다.
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.keyword_map = json.load(f)
        else:
            self.keyword_map = {}
            
        # LLM fallback을 위한 OpenAI 클라이언트 초기화 (.env에 OPENAI_API_KEY가 있다고 가정)
        try:
            self.llm_client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
        except Exception:
            self.llm_client = None

    def _get_llm_category(self, store_name: str) -> str:
        """3단계: LLM Fallback (전혀 모르는 가맹점일 경우)"""
        if not self.llm_client:
            return "ETC"
            
        try:
            # P01~P10 카테고리 설명을 프롬프트에 제공하여 매칭
            categories_desc = ", ".join([f"{k}({v[0]} 등)" for k, v in self.keyword_map.items()])
            prompt = f"다음 상호명이 어느 카테고리에 속하는지 P01부터 P10 중에서 하나만 출력하세요. 속하는 곳이 전혀 없다면 ETC를 출력하세요. 카테고리 정보: {categories_desc}"
            
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": store_name}
                ],
                temperature=0.0,
                max_tokens=10
            )
            result = response.choices[0].message.content.strip()
            
            # 응답값이 유효한 카테고리인지 확인
            if result in self.keyword_map or result == "ETC":
                return result
        except Exception as e:
            print(f"LLM Fallback Error for {store_name}: {e}")
            
        return "ETC"

    def match_type(self, row) -> str:
        """가맹점명을 기반으로 type_id를 반환하는 다단계 매칭 로직"""
        store_name = str(row.get('storeName', ''))
        subcategory = str(row.get('subcategory', ''))
        category = str(row.get('category', ''))
        
        # 0. 핵심: 소비리포트(category)와의 일맥상통을 위한 1차 매핑
        sub_to_p = {
            'delivery': 'P01', 'convenience_store': 'P02',
            'ott': 'P04', 'music': 'P04', 'taxi': 'P05',
            'health_beauty': 'P06', 'cafe': 'P07',
            'fashion': 'P08', 'ecommerce': 'P08',
            'book': 'P09', 'course': 'P09', 'academy': 'P09',
            'groceries': 'P10',
            'flight': 'P11', 'hotel': 'P11', 'package': 'P11',
            'movie': 'P13', 'hobby': 'P13', 'gaming': 'P13'
        }
        if subcategory in sub_to_p:
            return sub_to_p[subcategory]

        # 1. Exact/Keyword Match (빠른 경로)
        for t_id, keywords in self.keyword_map.items():
            if any(kw in store_name for kw in keywords):
                return t_id
                
        # 2. Fuzzy Match (형태소/문자열 유사도 기반)
        all_keywords = {kw: t_id for t_id, keywords in self.keyword_map.items() for kw in keywords}
        matches = difflib.get_close_matches(store_name, all_keywords.keys(), n=1, cutoff=0.6)
        if matches:
            return all_keywords[matches[0]]
            
        # 3. LLM API Fallback
        return self._get_llm_category(store_name)

    def preprocess(self, raw_data):
        """1단계: 가맹점명 기반 type_id 다단계 매핑 및 데이터 정제"""
        df = pd.DataFrame(raw_data)
        # apply 함수에 행 자체를 넘기기 위해 axis=1 설정
        df['type_id'] = df.apply(self.match_type, axis=1)
        df['amount'] = pd.to_numeric(df['amount'])
        return df

    def get_persona_score(self, df):
        """2단계: 금액(70%)과 빈도(30%) 가중치를 적용한 페르소나 산출"""
        stats = df.groupby('type_id').agg(
            total_amount=('amount', 'sum'),
            count=('amount', 'count')
        ).to_dict('index')

        scored_personas = []
        for p in self.personas:
            t_id = p['type_id']
            stat = stats.get(t_id, {'total_amount': 0, 'count': 0})
            
            # 결제 횟수당 만원 단위 가중치 부여
            score = (stat['total_amount'] * 0.7) + (stat['count'] * 10000 * 0.3)
            if score > 0:
                scored_personas.append({**p, **stat, "score": int(score)})

        scored_personas.sort(key=lambda x: x['score'], reverse=True)
        return scored_personas[0] if scored_personas else None, stats

    def simulate_benefits(self, stats, total_spend):
        """3단계: 동적 JSON 구조(혜택)를 통한 실질 절약액 시뮬레이션 계산"""
        simulation_results = []

        for card in self.cards:
            savings = 0
            
            # 혜택 정보가 구조화된 JSON (structural arrays) 형태라고 가정하고 파싱
            structured_benefits = card.get('benefits', {}).get('structured', [])
            
            for benefit in structured_benefits:
                target_type = benefit.get('target_type')
                rate = benefit.get('rate', 0.0)
                
                if target_type in stats:
                    savings += stats[target_type]['total_amount'] * rate
            
            benefits = card.get('benefits', {})
            simulation_results.append({
                "card_id": card.get('card_id'),
                "name": card.get('name'),
                "main_text": benefits.get('main_text', ''),
                "sub_text": benefits.get('sub_text', []),
                "estimated_savings": int(savings),
                "picking_rate": round((savings / total_spend) * 100, 2) if total_spend > 0 else 0,
                "comment": card.get('recommend_comment')
            })

        simulation_results.sort(key=lambda x: x['estimated_savings'], reverse=True)
        return simulation_results

    def run(self, raw_data):
        """최종 실행 파이프라인 메소드"""
        df = self.preprocess(raw_data)
        total_spend = df['amount'].sum()
        user_persona, stats = self.get_persona_score(df)
        recommendations = self.simulate_benefits(stats, total_spend)
        best_card = recommendations[0] if recommendations and recommendations[0]['estimated_savings'] > 0 else None
        
        return {
            "user_persona": user_persona,
            "best_card": best_card,
            "all_cards": recommendations,
            "total_spend": int(total_spend)
        }