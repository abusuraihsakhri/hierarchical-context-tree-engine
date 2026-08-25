"""
Tree Diff Visualization for Hierarchical Context Tree Engine.
Computes structural diffs between two tree snapshots and renders ASCII visualizations.
"""
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum


class DiffAction(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffNode:
    """Represents a single node difference."""
    node_id: str
    action: DiffAction
    path: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    children_diffs: List['DiffNode'] = field(default_factory=list)


@dataclass
class TreeSnapshot:
    """A stored tree snapshot with metadata."""
    snapshot_id: str
    tree: Dict[str, Any]
    created_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class TreeDiffEngine:
    """Computes and visualizes diffs between context tree snapshots."""

    def __init__(self):
        self._snapshots: Dict[str, TreeSnapshot] = {}

    def take_snapshot(self, tree: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a tree snapshot and return its ID."""
        snapshot_id = f"snap-{uuid.uuid4().hex[:8]}"
        self._snapshots[snapshot_id] = TreeSnapshot(
            snapshot_id=snapshot_id,
            tree=self._deep_copy(tree),
            created_at=time.time(),
            metadata=metadata or {},
        )
        return snapshot_id

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a stored snapshot by ID."""
        snap = self._snapshots.get(snapshot_id)
        return self._deep_copy(snap.tree) if snap else None

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all stored snapshots with metadata."""
        return [
            {
                "snapshot_id": s.snapshot_id,
                "created_at": s.created_at,
                "node_count": self._count_nodes(s.tree),
                "metadata": s.metadata,
            }
            for s in self._snapshots.values()
        ]

    def compute_diff(self, snapshot_a_id: str, snapshot_b_id: str) -> Dict[str, Any]:
        """Compute structural diff between two snapshots."""
        tree_a = self.get_snapshot(snapshot_a_id)
        tree_b = self.get_snapshot(snapshot_b_id)
        if tree_a is None:
            raise ValueError(f"Snapshot not found: {snapshot_a_id}")
        if tree_b is None:
            raise ValueError(f"Snapshot not found: {snapshot_b_id}")

        diff_root = self._diff_nodes(tree_a, tree_b, path="root")
        return {
            "snapshot_a": snapshot_a_id,
            "snapshot_b": snapshot_b_id,
            "diff": self._diff_node_to_dict(diff_root),
            "summary": self._summarize_diff(diff_root),
        }

    def render_ascii(self, diff_result: Dict[str, Any]) -> str:
        """Render a diff result as an ASCII tree visualization."""
        lines = [
            f"Tree Diff: {diff_result['snapshot_a']} -> {diff_result['snapshot_b']}",
            "=" * 60,
        ]
        summary = diff_result["summary"]
        lines.append(f"  Added: {summary['added']}, Removed: {summary['removed']}, "
                      f"Modified: {summary['modified']}, Unchanged: {summary['unchanged']}")
        lines.append("-" * 60)
        self._render_node_ascii(diff_result["diff"], lines, prefix="", is_last=True)
        return "\n".join(lines)

    def _diff_nodes(self, node_a: Dict[str, Any], node_b: Dict[str, Any], path: str) -> DiffNode:
        """Recursively diff two tree nodes."""
        id_a = node_a.get("node_id", node_a.get("id", ""))
        id_b = node_b.get("node_id", node_b.get("id", ""))

        # Check if values differ
        val_a = {k: v for k, v in node_a.items() if k != "children"}
        val_b = {k: v for k, v in node_b.items() if k != "children"}
        is_modified = val_a != val_b

        children_a = {c.get("node_id", c.get("id", str(i))): c for i, c in enumerate(node_a.get("children", []))}
        children_b = {c.get("node_id", c.get("id", str(i))): c for i, c in enumerate(node_b.get("children", []))}

        all_keys = set(children_a.keys()) | set(children_b.keys())
        children_diffs = []
        for key in sorted(all_keys):
            child_path = f"{path}/{key}"
            if key in children_a and key in children_b:
                children_diffs.append(self._diff_nodes(children_a[key], children_b[key], child_path))
            elif key in children_b:
                children_diffs.append(DiffNode(
                    node_id=key, action=DiffAction.ADDED, path=child_path,
                    new_value=children_b[key],
                ))
            else:
                children_diffs.append(DiffNode(
                    node_id=key, action=DiffAction.REMOVED, path=child_path,
                    old_value=children_a[key],
                ))

        has_child_changes = any(d.action != DiffAction.UNCHANGED for d in children_diffs)
        action = DiffAction.MODIFIED if (is_modified or has_child_changes) else DiffAction.UNCHANGED

        return DiffNode(
            node_id=id_a or id_b,
            action=action,
            path=path,
            old_value=val_a if is_modified else None,
            new_value=val_b if is_modified else None,
            children_diffs=children_diffs,
        )

    def _summarize_diff(self, diff: DiffNode) -> Dict[str, int]:
        counts = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}
        self._count_diff_actions(diff, counts)
        return counts

    def _count_diff_actions(self, node: DiffNode, counts: Dict[str, int]) -> None:
        counts[node.action.value] += 1
        for child in node.children_diffs:
            self._count_diff_actions(child, counts)

    def _diff_node_to_dict(self, node: DiffNode) -> Dict[str, Any]:
        return {
            "node_id": node.node_id,
            "action": node.action.value,
            "path": node.path,
            "old_value": node.old_value,
            "new_value": node.new_value,
            "children": [self._diff_node_to_dict(c) for c in node.children_diffs],
        }

    def _render_node_ascii(self, node: Dict[str, Any], lines: List[str], prefix: str, is_last: bool) -> None:
        action = node["action"]
        symbols = {"added": "+", "removed": "-", "modified": "~", "unchanged": " "}
        symbol = symbols.get(action, "?")
        connector = "\\-- " if is_last else "|-- "
        lines.append(f"{prefix}{connector}[{symbol}] {node['node_id']} ({action})")

        if node.get("old_value") and node.get("new_value"):
            lines.append(f"{prefix}{'    ' if is_last else '|   '}  old: {json.dumps(node['old_value'], default=str)[:80]}")
            lines.append(f"{prefix}{'    ' if is_last else '|   '}  new: {json.dumps(node['new_value'], default=str)[:80]}")

        children = node.get("children", [])
        for i, child in enumerate(children):
            extension = "    " if is_last else "|   "
            self._render_node_ascii(child, lines, prefix + extension, i == len(children) - 1)

    def _deep_copy(self, obj: Any) -> Any:
        return json.loads(json.dumps(obj, default=str))

    def _count_nodes(self, tree: Dict[str, Any]) -> int:
        count = 1
        for child in tree.get("children", []):
            count += self._count_nodes(child)
        return count
