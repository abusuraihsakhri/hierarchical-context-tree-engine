"""
Tree Pruning Strategies for Hierarchical Context Tree Engine.
Implements pluggable pruning strategies: DepthPruner, RelevancePruner, AgePruner, SizePruner.
"""
import time
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from .models import FrontierPayload, ExecutionStatus


class PruningStrategy(ABC):
    """Base interface for all pruning strategies."""

    @abstractmethod
    def should_prune(self, node: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Return True if the node should be pruned."""
        pass

    @abstractmethod
    def name(self) -> str:
        pass


@dataclass
class DepthPruner(PruningStrategy):
    """Remove branches exceeding max depth."""
    max_depth: int = 10

    def should_prune(self, node: Dict[str, Any], context: Dict[str, Any]) -> bool:
        depth = node.get("depth", 0)
        return depth > self.max_depth

    def name(self) -> str:
        return f"DepthPruner(max_depth={self.max_depth})"


@dataclass
class RelevancePruner(PruningStrategy):
    """Remove branches below relevance threshold."""
    min_relevance: float = 0.15

    def should_prune(self, node: Dict[str, Any], context: Dict[str, Any]) -> bool:
        relevance = node.get("relevance_score", 1.0)
        return relevance < self.min_relevance

    def name(self) -> str:
        return f"RelevancePruner(min_relevance={self.min_relevance})"


@dataclass
class AgePruner(PruningStrategy):
    """Remove branches older than max age (seconds)."""
    max_age_seconds: float = 3600.0

    def should_prune(self, node: Dict[str, Any], context: Dict[str, Any]) -> bool:
        created_at = node.get("created_at", 0)
        current_time = context.get("current_time", time.time())
        return (current_time - created_at) > self.max_age_seconds

    def name(self) -> str:
        return f"AgePruner(max_age={self.max_age_seconds}s)"


@dataclass
class SizePruner(PruningStrategy):
    """Remove branches exceeding token budget."""
    max_tokens: int = 4096

    def should_prune(self, node: Dict[str, Any], context: Dict[str, Any]) -> bool:
        token_count = node.get("token_count", 0)
        return token_count > self.max_tokens

    def name(self) -> str:
        return f"SizePruner(max_tokens={self.max_tokens})"


class CompositePruner:
    """Combine multiple pruners with priority ordering."""

    def __init__(self, strategies: Optional[List[PruningStrategy]] = None):
        self.strategies: List[PruningStrategy] = strategies or []
        self._prune_log: List[Dict[str, Any]] = []

    def add_strategy(self, strategy: PruningStrategy, priority: int = 0) -> None:
        self.strategies.append(strategy)
        self.strategies.sort(key=lambda s: getattr(s, 'priority', 0))

    def should_prune(self, node: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> bool:
        ctx = context or {"current_time": time.time()}
        for strategy in self.strategies:
            if strategy.should_prune(node, ctx):
                self._prune_log.append({
                    "node_id": node.get("node_id", "unknown"),
                    "strategy": strategy.name(),
                    "timestamp": time.time(),
                })
                return True
        return False

    def prune_tree(self, tree: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Recursively prune a tree structure."""
        ctx = context or {"current_time": time.time()}
        if self.should_prune(tree, ctx):
            return None

        pruned_children = []
        for child in tree.get("children", []):
            result = self.prune_tree(child, ctx)
            if result is not None:
                pruned_children.append(result)
        tree["children"] = pruned_children
        return tree

    def get_prune_log(self) -> List[Dict[str, Any]]:
        return list(self._prune_log)

    def get_strategy_names(self) -> List[str]:
        return [s.name() for s in self.strategies]


# Factory for CLI integration
STRATEGY_REGISTRY: Dict[str, Callable[..., PruningStrategy]] = {
    "depth": lambda cfg: DepthPruner(max_depth=cfg.get("max_depth", 10)),
    "relevance": lambda cfg: RelevancePruner(min_relevance=cfg.get("min_relevance", 0.15)),
    "age": lambda cfg: AgePruner(max_age_seconds=cfg.get("max_age_seconds", 3600)),
    "size": lambda cfg: SizePruner(max_tokens=cfg.get("max_tokens", 4096)),
}


def create_pruner(strategy_name: str, config: Optional[Dict[str, Any]] = None) -> PruningStrategy:
    """Factory function to create a pruner by name."""
    cfg = config or {}
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown pruning strategy: {strategy_name}. Available: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[strategy_name](cfg)


def create_composite_pruner(strategy_names: List[str], config: Optional[Dict[str, Any]] = None) -> CompositePruner:
    """Create a composite pruner from multiple strategy names."""
    cfg = config or {}
    pruner = CompositePruner()
    for name in strategy_names:
        pruner.add_strategy(create_pruner(name, cfg))
    return pruner
