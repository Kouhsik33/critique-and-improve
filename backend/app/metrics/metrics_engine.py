"""
Metrics Engine for tracking idea, agent, and system-level metrics.
Calculates and stores metrics throughout the workflow lifecycle.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import math

from app.db.postgres import DatabaseManager, AgentMetric
from app.schemas.state_schema import WorkflowState


@dataclass
class IdeaMetrics:
    """Metrics for a single idea"""
    novelty: float  # How original/unique (0-1)
    feasibility: float  # How practical (0-1)
    clarity: float  # How well-expressed (0-1)
    impact: float  # Potential impact (0-1)
    fitness_score: float = 0.0
    
    def calculate_fitness(self) -> float:
        """Calculate overall fitness score"""
        self.fitness_score = (self.novelty + self.feasibility + self.clarity + self.impact) / 4
        return self.fitness_score


@dataclass
class AgentMetrics:
    """Metrics for a single agent"""
    token_count: int = 0
    quality_score: float = 0.0
    confidence: float = 0.5
    diversity_score: Optional[float] = None
    accuracy: Optional[float] = None
    latency_ms: float = 0.0


@dataclass
class SystemMetrics:
    """System-level metrics"""
    iteration_count: int = 0
    convergence_speed: Optional[float] = None
    total_token_usage: int = 0
    conflict_intensity: float = 0.0
    token_efficiency: float = 0.0


class MetricsCalculator:
    """Calculates metrics for ideas and agents"""
    
    @staticmethod
    def calculate_idea_metrics(
        idea: str,
        critiques: List[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> IdeaMetrics:
        """
        Calculate metrics for an idea.
        
        Novelty: Based on uniqueness compared to history
        Feasibility: Based on critical feedback severity
        Clarity: Based on idea length and structure
        Impact: Based on sentiment and scope
        """
        metrics = IdeaMetrics(
            novelty=MetricsCalculator._calculate_novelty(idea, history),
            feasibility=MetricsCalculator._calculate_feasibility(idea, critiques),
            clarity=MetricsCalculator._calculate_clarity(idea),
            impact=MetricsCalculator._calculate_impact(idea),
        )
        metrics.calculate_fitness()
        return metrics
    
    @staticmethod
    def _calculate_novelty(idea: str, history: Optional[List[Dict[str, Any]]]) -> float:
        """Calculate novelty score (0-1)"""
        if not history:
            return 0.8  # High novelty if no history
        
        # Simple heuristic: check for word overlap with previous ideas
        prev_ideas = [h.get("idea", "") for h in history if h.get("type") == "idea"]
        if not prev_ideas:
            return 0.8
        
        idea_words = set(idea.lower().split())
        max_overlap = 0
        
        for prev in prev_ideas:
            prev_words = set(prev.lower().split())
            overlap = len(idea_words & prev_words) / len(idea_words | prev_words) if idea_words else 0
            max_overlap = max(max_overlap, overlap)
        
        # Lower overlap = higher novelty
        return 1.0 - (max_overlap * 0.7)
    
    @staticmethod
    def _calculate_feasibility(idea: str, critiques: Optional[List[str]]) -> float:
        """Calculate feasibility score (0-1)"""
        if not critiques:
            return 0.5  # Neutral if no critiques
        
        # Count negative keywords in critiques
        negative_keywords = [
            "impossible", "unfeasible", "impractical", "not viable",
            "won't work", "unrealistic", "not executable", "problematic"
        ]
        
        critique_text = " ".join(critiques).lower()
        negative_count = sum(1 for kw in negative_keywords if kw in critique_text)
        
        feasibility = max(0, 0.6 - (negative_count * 0.1))
        return feasibility
    
    @staticmethod
    def _calculate_clarity(idea: str) -> float:
        """Calculate clarity score (0-1)"""
        # Heuristic: structure, length, complexity
        sentences = len([s for s in idea.split(".") if s.strip()])
        words = len(idea.split())
        
        # Optimal: 3-8 sentences, 50-300 words
        sentence_score = 1 - abs(sentences - 5) / 10 if sentences > 0 else 0
        word_score = 1 - abs(words - 150) / 200 if words > 0 else 0
        
        clarity = (sentence_score + word_score) / 2
        return max(0, min(1, clarity))
    
    @staticmethod
    def _calculate_impact(idea: str) -> float:
        """Calculate impact score (0-1)"""
        # Heuristic: presence of action verbs and scope indicators
        action_verbs = [
            "transform", "revolutionize", "improve", "enhance", "accelerate",
            "reduce", "eliminate", "create", "develop", "scale"
        ]
        
        scope_indicators = [
            "industry", "market", "global", "widespread", "fundamental",
            "game-changing", "breakthrough", "innovative"
        ]
        
        idea_lower = idea.lower()
        verb_count = sum(1 for v in action_verbs if v in idea_lower)
        scope_count = sum(1 for s in scope_indicators if s in idea_lower)
        
        impact = (verb_count * 0.05 + scope_count * 0.08)
        return min(1.0, impact)
    
    @staticmethod
    def calculate_agent_quality(
        agent: str,
        output: str,
        feedback_score: float = 0.5,
        token_count: int = 0,
    ) -> AgentMetrics:
        """Calculate quality metrics for agent output"""
        metrics = AgentMetrics(
            token_count=token_count,
            quality_score=MetricsCalculator._calculate_agent_quality_score(
                agent, output, feedback_score
            ),
            confidence=MetricsCalculator._calculate_confidence(output),
        )
        return metrics
    
    @staticmethod
    def _calculate_agent_quality_score(
        agent: str,
        output: str,
        feedback_score: float,
    ) -> float:
        """Calculate agent output quality (0-1)"""
        # Agent-specific quality heuristics
        base_score = feedback_score  # 0-1
        
        # Length quality (should have substantial content)
        word_count = len(output.split())
        length_factor = min(1.0, word_count / 100)
        
        scores = {
            "creator": base_score * 0.7 + length_factor * 0.3,
            "critic": min(1.0, base_score * 0.8 + (1 - feedback_score) * 0.2),  # Critics do well when finding issues
            "radical": base_score * 0.6 + length_factor * 0.4,  # Radical valued for quantity
            "synthesizer": base_score * 0.9 + 0.1 * length_factor,  # Synthesizer needs quality
            "judge": base_score * 0.95,  # Judge is most critical
        }
        
        return scores.get(agent, base_score)
    
    @staticmethod
    def _calculate_confidence(output: str) -> float:
        """Calculate confidence in the output (0-1)"""
        # Heuristic: presence of confident language
        confident_phrases = [
            "definitely", "certainly", "clearly", "obviously", "without doubt",
            "it's clear", "strongly", "must", "will", "proven"
        ]
        
        uncertain_phrases = [
            "might", "perhaps", "maybe", "could", "somewhat",
            "seems", "appears", "may be", "unclear", "uncertain"
        ]
        
        output_lower = output.lower()
        confidence_count = sum(1 for p in confident_phrases if p in output_lower)
        uncertainty_count = sum(1 for p in uncertain_phrases if p in output_lower)
        
        confidence = (confidence_count - uncertainty_count) / max(1, confidence_count + uncertainty_count + 1)
        return max(0, min(1, 0.5 + confidence * 0.5))


class MetricsEngine:
    """Main metrics engine for tracking throughout workflow"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.idea_metrics: List[IdeaMetrics] = []
        self.agent_metrics: Dict[str, List[AgentMetrics]] = {
            "creator": [],
            "critic": [],
            "radical": [],
            "synthesizer": [],
            "judge": [],
        }
        self.system_metrics: SystemMetrics = SystemMetrics()
        self.iteration_times: List[float] = []
    
    def record_idea_metrics(
        self,
        iteration: int,
        idea: str,
        critiques: List[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ):
        """Record metrics for an idea"""
        metrics = MetricsCalculator.calculate_idea_metrics(idea, critiques, history)
        self.idea_metrics.append(metrics)
        
        # Store in database
        DatabaseManager.log_idea_metric(
            workflow_id=self.workflow_id,
            iteration=iteration,
            idea=idea,
            novelty=metrics.novelty,
            feasibility=metrics.feasibility,
            clarity=metrics.clarity,
            impact=metrics.impact,
        )
    
    def record_agent_output(
        self,
        iteration: int,
        agent: str,
        output: str,
        token_count: int = 0,
        feedback_score: float = 0.5,
        action: str = "generate",
    ):
        """Record agent output metrics"""
        metrics = MetricsCalculator.calculate_agent_quality(
            agent, output, feedback_score, token_count
        )
        
        if agent in self.agent_metrics:
            self.agent_metrics[agent].append(metrics)
        
        self.system_metrics.total_token_usage += token_count
        
        # Store in database
        DatabaseManager.log_agent_metric(
            workflow_id=self.workflow_id,
            agent=agent,
            iteration=iteration,
            action=action,
            token_count=token_count,
            quality_score=metrics.quality_score,
            confidence=metrics.confidence,
            output=output,
        )
    
    def calculate_convergence_speed(self, iterations: int) -> float:
        """Calculate how quickly the system is converging"""
        if len(self.idea_metrics) < 2 or iterations == 0:
            return 0.0
        
        # Check if fitness scores are improving and stabilizing
        recent_scores = [m.fitness_score for m in self.idea_metrics[-3:]]
        historical_scores = [m.fitness_score for m in self.idea_metrics[:-3]]
        
        if not historical_scores:
            return 0.0
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        historical_avg = sum(historical_scores) / len(historical_scores)
        improvement = (recent_avg - historical_avg) / max(0.0001, historical_avg)
        
        # Convergence speed = improvement / iterations
        return max(0, min(1, improvement / iterations))
    
    def calculate_conflict_intensity(self) -> float:
        """Calculate system-level conflict (disagreement between agents)"""
        if len(self.idea_metrics) < 1:
            return 0.0
        
        # Heuristic: based on variation in fitness scores and number of iterations
        if len(self.idea_metrics) < 2:
            return 0.5
        
        scores = [m.fitness_score for m in self.idea_metrics]
        variance = sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores)
        
        # Normalize to 0-1
        conflict = min(1.0, math.sqrt(variance))
        return conflict
    
    def finalize_metrics(self, iteration_count: int, total_tokens: int):
        """Finalize metrics at end of workflow"""
        self.system_metrics.iteration_count = iteration_count
        self.system_metrics.total_token_usage = total_tokens
        self.system_metrics.convergence_speed = self.calculate_convergence_speed(iteration_count)
        self.system_metrics.conflict_intensity = self.calculate_conflict_intensity()
        self.system_metrics.token_efficiency = total_tokens / max(1, iteration_count)
        
        # Store system metrics
        DatabaseManager.log_system_metric(
            workflow_id=self.workflow_id,
            iteration_count=iteration_count,
            total_token_usage=total_tokens,
            conflict_intensity=self.system_metrics.conflict_intensity,
            convergence_speed=self.system_metrics.convergence_speed,
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "idea_metrics": [
                {
                    "novelty": m.novelty,
                    "feasibility": m.feasibility,
                    "clarity": m.clarity,
                    "impact": m.impact,
                    "fitness_score": m.fitness_score,
                }
                for m in self.idea_metrics
            ],
            "agent_metrics": {
                agent: [
                    {
                        "token_count": m.token_count,
                        "quality_score": m.quality_score,
                        "confidence": m.confidence,
                    }
                    for m in metrics
                ]
                for agent, metrics in self.agent_metrics.items()
            },
            "system_metrics": {
                "iteration_count": self.system_metrics.iteration_count,
                "convergence_speed": self.system_metrics.convergence_speed,
                "total_token_usage": self.system_metrics.total_token_usage,
                "conflict_intensity": self.system_metrics.conflict_intensity,
                "token_efficiency": self.system_metrics.token_efficiency,
            },
        }
