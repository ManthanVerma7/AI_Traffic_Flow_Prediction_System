import math
import re
from collections import Counter

class SimpleRAG:
    """
    A lightweight Retrieval-Augmented Generation (RAG) engine.
    Uses TF-IDF / Cosine Similarity to find the most relevant context 
    from the generated pipeline results without crashing low-end CPUs.
    """
    def __init__(self):
        self.knowledge_base = []
        self.kb_tokens = []
    
    def build_knowledge_base(self, analysis_results):
        if not analysis_results:
            return
            
        kb = [
            f"The video analyzed is named {analysis_results.get('video_name', 'unknown')}.",
            f"A total of {analysis_results.get('processed_frames', 0)} frames were processed.",
            f"The peak traffic (maximum observed) in a single frame was {analysis_results.get('max_veh', 0)} vehicles.",
            f"The average number of vehicles per frame is {analysis_results.get('avg_veh', 0)}.",
            f"The current traffic level is classified as {analysis_results.get('traffic_level', 'UNKNOWN')}.",
            f"The pipeline processing took {analysis_results.get('processing_time', 0)} seconds.",
            f"We predicted {analysis_results.get('pred_steps', 200)} steps into the future, with an average predicted traffic of {analysis_results.get('avg_pred', 0)}."
        ]
        
        dist = analysis_results.get("graph_data", {}).get("distribution", {})
        if dist:
            for vehicle, count in dist.items():
                kb.append(f"There were {count} {vehicle} detected in total throughout the video.")
                
            top_vehicle = max(dist, key=dist.get)
            kb.append(f"The most dominant vehicle type in the traffic was {top_vehicle}.")
        
        # Causal reasoning for RAG
        avg_v = analysis_results.get('avg_veh', 0)
        if avg_v > 40:
            kb.append("The congestion is high because the average vehicle count exceeded the normal road capacity threshold.")
        else:
            kb.append("The congestion is low because the average vehicle density remains below structural limits.")
            
        if analysis_results.get('avg_pred', 0) > avg_v:
            kb.append("The prediction increased because historical lagging data indicates an upward momentum in incoming traffic density.")
        else:
            kb.append("The prediction is stable or decreasing because recent frames showed a drop in vehicle density.")
            
        self.knowledge_base = kb
        self.kb_tokens = [self._tokenize(doc) for doc in kb]

    def _tokenize(self, text):
        return re.findall(r'\w+', text.lower())

    def _cosine_similarity(self, vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator: return 0.0
        return float(numerator) / denominator

    def answer_query(self, query):
        if not self.knowledge_base:
            return "I don't have any traffic data loaded yet. Please process a video first."
            
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return "Please ask a valid question."
            
        query_vec = Counter(query_tokens)
        
        best_score = 0
        best_match = ""
        
        for i, doc_tokens in enumerate(self.kb_tokens):
            doc_vec = Counter(doc_tokens)
            score = self._cosine_similarity(query_vec, doc_vec)
            if score > best_score:
                best_score = score
                best_match = self.knowledge_base[i]
                
        if best_score < 0.05:
            # Fallback heuristic reasoning
            if "why" in query_tokens and "congestion" in query_tokens:
                return "Congestion levels are dictated by the average vehicle count crossing structural capacity thresholds."
            return "I'm sorry, I couldn't find specific data in the latest analysis to answer that. Try asking about max vehicles, averages, or predictions."
            
        return best_match
