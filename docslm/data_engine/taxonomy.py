"""Capability taxonomy — STRICT UNIFORM sampling.

Every implemented (skill, route) capability gets an identical number of tasks:
assignment is a deterministic round-robin over the capability list (index % N),
with difficulty cycling 1-2-3 uniformly. Scenes are uniform within a capability.
This guarantees equal training volume per function group ("identical
performance" weighting) instead of random weights that drift.

English-only: lang is always en-US.
"""
from dataclasses import dataclass, asdict
import random

# (skill, route, scenes) — order defines the round-robin cycle.
CAPABILITIES = [
    # docx
    ("docx", "create", ["report", "contract", "resume", "exam", "academic", "official-doc", "copywriting"]),
    ("docx", "edit", ["report", "contract", "resume"]),
    ("docx", "format", ["report", "resume", "academic"]),
    ("docx", "read", ["report", "contract", "exam"]),
    ("docx", "toc_fix", ["report", "academic"]),
    ("docx", "footer_fix", ["report", "contract"]),
    ("docx", "comment", ["report", "contract"]),
    # pdf
    ("pdf", "report", ["business-report", "certificate"]),
    ("pdf", "merge", ["process"]),
    ("pdf", "split", ["process"]),
    ("pdf", "rotate", ["process"]),
    ("pdf", "crop", ["process"]),
    ("pdf", "extract_text", ["process"]),
    ("pdf", "extract_table", ["process"]),
    ("pdf", "extract_image", ["process"]),
    ("pdf", "form_fill", ["process"]),
    ("pdf", "meta_edit", ["process"]),
    ("pdf", "font_check", ["business-report"]),
    ("pdf", "toc_check", ["business-report"]),
    ("pdf", "palette", ["business-report"]),
    ("pdf", "qa", ["business-report"]),
    # xlsx
    ("xlsx", "create", ["finance", "analyze", "general"]),
    ("xlsx", "edit", ["finance", "general"]),
    ("xlsx", "analyze", ["analyze", "finance"]),
    ("xlsx", "inspect", ["general", "finance"]),
    ("xlsx", "scan", ["general", "finance"]),
    ("xlsx", "audit", ["finance", "general"]),
    ("xlsx", "pivot", ["analyze"]),
    # pptx
    ("pptx", "create", ["pitch", "report", "training"]),
    ("pptx", "inspect_edit", ["report", "training"]),
]

N_CAPS = len(CAPABILITIES)
DIFFICULTY_CYCLE = [1, 2, 3]


@dataclass
class TaskSpec:
    task_id: str
    seed: int
    skill: str
    route: str
    scene: str
    lang: str
    difficulty: int

    def stratum(self) -> dict:
        return {"skill": self.skill, "route": self.route, "scene": self.scene,
                "lang": self.lang, "difficulty": self.difficulty}

    def to_dict(self) -> dict:
        return asdict(self)


def capability_at(index: int) -> tuple:
    return CAPABILITIES[index % N_CAPS]


def sample_task(rng: random.Random, index: int) -> TaskSpec:
    """Deterministic capability + difficulty by index (exact equality);
    scene uniform within capability; lang fixed en-US."""
    skill, route, scenes = capability_at(index)
    return TaskSpec(
        task_id=f"task_{index:06d}",
        seed=rng.randrange(2**31),
        skill=skill, route=route,
        scene=rng.choice(scenes),
        lang="en-US",
        difficulty=DIFFICULTY_CYCLE[index % 3],
    )
