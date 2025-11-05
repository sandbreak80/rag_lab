"""
Topic Classifier - Classify queries by topic and enforce use case policies
"""

import re
from typing import Dict, List

class TopicClassifier:
    """
    Rule-based topic classification with policy enforcement

    Note: For production, consider fine-tuning DistilBERT for better accuracy
    """

    def __init__(self):
        # Topic definitions with keywords
        self.topics = {
            # Allowed topics
            'rag_architecture': {
                'keywords': ['rag', 'retrieval', 'augmented', 'generation', 'vector', 'embedding', 'search'],
                'allowed': True
            },
            'ai_ml_concepts': {
                'keywords': ['ai', 'ml', 'machine learning', 'neural network', 'transformer', 'llm', 'model'],
                'allowed': True
            },
            'technical_architecture': {
                'keywords': ['architecture', 'system', 'design', 'microservice', 'api', 'database'],
                'allowed': True
            },
            'security_best_practices': {
                'keywords': ['security', 'authentication', 'encryption', 'compliance', 'privacy'],
                'allowed': True
            },

            # Disallowed topics
            'medical_advice': {
                'keywords': ['diagnosis', 'treatment', 'medication', 'symptoms', 'disease', 'doctor', 'health'],
                'allowed': False,
                'message': "I cannot provide medical advice. Please consult a healthcare professional."
            },
            'legal_advice': {
                'keywords': ['legal', 'lawsuit', 'contract', 'attorney', 'litigation', 'lawyer'],
                'allowed': False,
                'message': "I cannot provide legal advice. Please consult a licensed attorney."
            },
            'financial_advice': {
                'keywords': ['investment', 'stock', 'trading', 'financial planning', 'tax advice'],
                'allowed': False,
                'message': "I cannot provide financial advice. Please consult a financial advisor."
            },
            'personal_relationships': {
                'keywords': ['dating', 'marriage', 'breakup', 'relationship advice'],
                'allowed': False,
                'message': "This system is designed for technical and educational queries."
            },
            'illegal_activities': {
                'keywords': ['hack', 'exploit', 'illegal', 'fraud', 'piracy', 'steal'],
                'allowed': False,
                'message': "I cannot assist with illegal activities."
            },
        }

        # Use case policies
        self.use_case_policies = {
            'educational': {
                'allowed_topics': ['rag_architecture', 'ai_ml_concepts', 'technical_architecture', 'security_best_practices'],
                'strict_mode': False
            },
            'demo': {
                'allowed_topics': ['rag_architecture', 'ai_ml_concepts', 'technical_architecture'],
                'strict_mode': True
            },
            'research': {
                'allowed_topics': 'all_except_disallowed',
                'strict_mode': False
            }
        }

    def classify(self, text: str, use_case: str = 'educational') -> Dict:
        """
        Classify query by topic and check against use case policy

        Returns:
            {
                'primary_topic': str,
                'topics': List[str],
                'confidence': float,
                'allowed': bool,
                'message': str  # If blocked
            }
        """
        text_lower = text.lower()
        topic_scores = {}

        # Calculate scores for each topic
        for topic_name, topic_info in self.topics.items():
            score = 0
            for keyword in topic_info['keywords']:
                if keyword.lower() in text_lower:
                    score += 1

            if score > 0:
                topic_scores[topic_name] = score

        # If no topics matched, default to allowed
        if not topic_scores:
            return {
                'primary_topic': 'general',
                'topics': ['general'],
                'confidence': 0.5,
                'allowed': True,
                'message': None
            }

        # Get primary topic (highest score)
        primary_topic = max(topic_scores, key=topic_scores.get)
        all_topics = list(topic_scores.keys())
        confidence = min(topic_scores[primary_topic] / 3.0, 1.0)  # Normalize to 0-1

        # Check policy
        topic_info = self.topics[primary_topic]
        policy = self.use_case_policies.get(use_case, self.use_case_policies['educational'])

        # Check if topic is allowed
        allowed = topic_info['allowed']

        # Check against use case policy
        if policy['allowed_topics'] != 'all_except_disallowed':
            if primary_topic not in policy['allowed_topics'] and allowed:
                allowed = not policy['strict_mode']  # Warn instead of block if not strict

        message = topic_info.get('message') if not allowed else None

        return {
            'primary_topic': primary_topic,
            'topics': all_topics,
            'confidence': confidence,
            'allowed': allowed,
            'message': message
        }

    def get_allowed_topics(self, use_case: str = 'educational') -> List[str]:
        """Get list of allowed topics for a use case"""
        policy = self.use_case_policies.get(use_case, self.use_case_policies['educational'])

        if policy['allowed_topics'] == 'all_except_disallowed':
            return [name for name, info in self.topics.items() if info['allowed']]
        else:
            return policy['allowed_topics']

