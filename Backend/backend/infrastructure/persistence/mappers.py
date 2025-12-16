from __future__ import annotations

from typing import Iterable

from app.models.ai_plan import AiPlanRun
from app.models.goal import Goal as GoalModel
from app.models.task import Task as TaskModel
from backend.domain.entities.goal import Goal
from backend.domain.entities.plan import Plan
from backend.domain.entities.task import Task


def task_to_model(task: Task) -> TaskModel:
    return TaskModel(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        estimated_minutes=task.estimated_minutes,
        energy_level=task.energy_level,
        goal_id=task.goal_id,
        due_at=task.due_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        deleted=task.deleted,
    )


def model_to_task(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        user_id=model.user_id,
        title=model.title,
        description=model.description,
        status=model.status,
        priority=model.priority,
        estimated_minutes=model.estimated_minutes,
        energy_level=model.energy_level,
        goal_id=model.goal_id,
        due_at=model.due_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted=model.deleted,
    )


def plan_to_model(plan: Plan) -> AiPlanRun:
    return AiPlanRun(
        id=plan.id,
        user_id=plan.user_id,
        plan_request_id=plan.id,
        status="generated",
        version=plan.version,
        request_payload={},
        response_payload={},
    )


def model_to_plan(model: AiPlanRun, tasks: Iterable[Task] | None = None) -> Plan:
    return Plan(id=model.id, user_id=model.user_id, tasks=list(tasks or []), version=model.version)


def goal_to_model(goal: Goal) -> GoalModel:
    return GoalModel(
        id=goal.id,
        user_id=goal.user_id,
        title=goal.title,
        description=goal.description,
        target_date=goal.target_date,
        progress=goal.progress,
        tasks_total=goal.tasks_total,
        tasks_completed=goal.tasks_completed,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
        deleted=goal.deleted,
    )


def model_to_goal(model: GoalModel) -> Goal:
    return Goal(
        id=model.id,
        user_id=model.user_id,
        title=model.title,
        description=model.description,
        target_date=model.target_date,
        progress=model.progress,
        tasks_total=model.tasks_total,
        tasks_completed=model.tasks_completed,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted=model.deleted,
    )
