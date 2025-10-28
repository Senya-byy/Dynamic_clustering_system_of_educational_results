# backend/repositories/cluster_repository.py
"""Персистентность запусков кластеризации (ClusterRun / ClusterAssignment)."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy.orm import joinedload

from models import db, ClusterRun, ClusterAssignment


class ClusterRunRepository:
    @staticmethod
    def create_run(
        group_id: int,
        n_clusters: int,
        assignments: List[dict],
        silhouette_score: Optional[float] = None,
    ) -> ClusterRun:
        """
        assignments: [{student_id, cluster_label, feature_vector: list[float]}]
        """
        run = ClusterRun(
            group_id=group_id,
            n_clusters=n_clusters,
            silhouette_score=silhouette_score,
        )
        db.session.add(run)
        db.session.flush()
        for row in assignments:
            fv = row.get('feature_vector')
            db.session.add(
                ClusterAssignment(
                    run_id=run.id,
                    student_id=int(row['student_id']),
                    cluster_label=int(row['cluster_label']),
                    feature_vector_json=json.dumps(fv) if fv is not None else None,
                )
            )
        db.session.commit()
        return run

    @staticmethod
    def find_run(run_id: int) -> Optional[ClusterRun]:
        return (
            ClusterRun.query.options(joinedload(ClusterRun.assignments))
            .filter_by(id=run_id)
            .first()
        )

    @staticmethod
    def list_runs_for_group(group_id: int) -> List[ClusterRun]:
        return (
            ClusterRun.query.options(joinedload(ClusterRun.assignments))
            .filter_by(group_id=group_id)
            .order_by(ClusterRun.created_at.asc())
            .all()
        )

    @staticmethod
    def list_assignments(run_id: int) -> List[ClusterAssignment]:
        return ClusterAssignment.query.filter_by(run_id=run_id).all()

    @staticmethod
    def distribution_for_run(run: ClusterRun) -> dict[str, int]:
        out: dict[str, int] = {}
        for a in run.assignments:
            k = str(a.cluster_label)
            out[k] = out.get(k, 0) + 1
        return out

    @staticmethod
    def parse_features(assignment: ClusterAssignment) -> Optional[List[float]]:
        if not assignment.feature_vector_json:
            return None
        try:
            return json.loads(assignment.feature_vector_json)
        except (json.JSONDecodeError, TypeError):
            return None


# Имя из C4 / задание (аналог «ClusterResultRepository»).
ClusterResultRepository = ClusterRunRepository
