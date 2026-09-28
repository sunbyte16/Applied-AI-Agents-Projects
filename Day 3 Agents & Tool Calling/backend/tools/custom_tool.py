"""
Custom Function Tool: Skill Gap Calculator for AgentLab AI.
Analyzes user skill sets against industry benchmark requirements for target technical roles.
"""

from typing import Any, Dict, List, Union
from backend.tools.base import BaseTool

ROLE_BENCHMARKS: Dict[str, Dict[str, List[str]]] = {
    "machine learning engineer": {
        "title": "Machine Learning Engineer",
        "core": ["Python", "SQL", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-Learn", "Docker", "Data Pipelines"],
        "recommended": ["MLOps", "FastAPI", "Git", "Mathematics & Statistics", "Kubernetes", "Model Evaluation"],
    },
    "data scientist": {
        "title": "Data Scientist",
        "core": ["Python", "SQL", "Statistics", "Machine Learning", "Pandas", "NumPy", "Data Visualization", "A/B Testing"],
        "recommended": ["Scikit-Learn", "BigQuery", "Tableau", "Storytelling", "Business Intelligence"],
    },
    "ai agent engineer": {
        "title": "AI Agent Engineer",
        "core": ["Python", "Prompt Engineering", "Tool Calling", "Function Calling", "Agent Orchestration", "FastAPI", "Vector Databases", "RAG"],
        "recommended": ["Pydantic", "AsyncIO", "LangGraph", "Multi-Agent Systems", "Evaluation Frameworks", "Docker"],
    },
    "full stack developer": {
        "title": "Full Stack Developer",
        "core": ["JavaScript", "TypeScript", "React", "Node.js", "HTML", "CSS", "SQL", "REST APIs", "Git"],
        "recommended": ["Next.js", "Tailwind CSS", "Docker", "PostgreSQL", "CI/CD"],
    },
    "cloud devops engineer": {
        "title": "Cloud DevOps Engineer",
        "core": ["Linux", "Docker", "Kubernetes", "Terraform", "CI/CD", "AWS", "GCP", "Bash", "Git"],
        "recommended": ["Python", "Prometheus", "Grafana", "Ansible", "Cloud Security"],
    },
}


def _normalize(text: str) -> str:
    """Normalize string for fuzzy comparison."""
    return text.lower().replace("-", "").replace("_", "").replace(" ", "").strip()


class SkillGapTool(BaseTool):
    """Custom developer-defined function to calculate skill gaps and job readiness."""

    name = "skill_gap_calculator"
    description = (
        "Analyze a candidate's current skills against standard industry benchmarks for a target role "
        "(such as 'Machine Learning Engineer', 'Data Scientist', 'AI Agent Engineer', 'Full Stack Developer', or 'Cloud DevOps Engineer'). "
        "Returns matched skills, missing core competencies, readiness percentage, and learning recommendations. "
        "Use this tool when users ask to evaluate their skills, find skill gaps, or check job readiness."
    )
    parameters = {
        "type": "object",
        "properties": {
            "target_role": {
                "type": "string",
                "description": "The target job title or role, e.g. 'Machine Learning Engineer', 'AI Agent Engineer', 'Data Scientist'.",
            },
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of skills currently possessed by the user, e.g. ['Python', 'SQL', 'TensorFlow'].",
            },
        },
        "required": ["target_role", "skills"],
    }

    def execute(self, target_role: str = "", skills: Union[List[str], str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Evaluate skill match against the benchmark."""
        if not target_role or not isinstance(target_role, str) or not target_role.strip():
            return {
                "tool": self.name,
                "success": False,
                "error": "target_role is required and must be a non-empty string.",
            }

        # Normalize skills into a list of strings
        user_skills_list: List[str] = []
        if isinstance(skills, list):
            user_skills_list = [str(s).strip() for s in skills if str(s).strip()]
        elif isinstance(skills, str):
            user_skills_list = [s.strip() for s in skills.split(",") if s.strip()]

        if not user_skills_list:
            return {
                "tool": self.name,
                "success": False,
                "error": "skills list must contain at least one skill.",
            }

        # Match target role in benchmarks
        clean_role_query = _normalize(target_role)
        matched_key = None
        for key in ROLE_BENCHMARKS:
            if _normalize(key) in clean_role_query or clean_role_query in _normalize(key):
                matched_key = key
                break

        if not matched_key:
            # Fallback to closest match or ML Engineer
            matched_key = "machine learning engineer"
            benchmark = ROLE_BENCHMARKS[matched_key]
            role_display = f"{target_role.strip()} (approximated with {benchmark['title']})"
        else:
            benchmark = ROLE_BENCHMARKS[matched_key]
            role_display = benchmark["title"]

        core_reqs = benchmark["core"]
        rec_reqs = benchmark["recommended"]

        # Check matched vs missing
        norm_user_skills = {_normalize(s): s for s in user_skills_list}

        matched: List[str] = []
        missing_core: List[str] = []

        for req in core_reqs:
            req_norm = _normalize(req)
            found = False
            for user_norm, original_user in norm_user_skills.items():
                if req_norm == user_norm or req_norm in user_norm or user_norm in req_norm:
                    matched.append(req)
                    found = True
                    break
            if not found:
                missing_core.append(req)

        missing_rec: List[str] = []
        for rec in rec_reqs:
            rec_norm = _normalize(rec)
            found = False
            for user_norm in norm_user_skills:
                if rec_norm == user_norm or rec_norm in user_norm or user_norm in rec_norm:
                    found = True
                    break
            if not found:
                missing_rec.append(rec)

        total_core = len(core_reqs)
        match_score = round((len(matched) / total_core) * 100, 1)

        if match_score >= 80:
            readiness = "High - Job Ready"
            recommendation = "Focus on portfolio projects, system design, and interview preparation."
        elif match_score >= 50:
            readiness = "Moderate - Progressing"
            recommendation = f"Prioritize mastering {', '.join(missing_core[:2])} to close core gaps."
        else:
            readiness = "Developing - Foundation Stage"
            recommendation = f"Build foundational competencies in {', '.join(missing_core[:3])}."

        return {
            "tool": self.name,
            "success": True,
            "target_role": role_display,
            "candidate_skills": user_skills_list,
            "matched_core_skills": matched,
            "missing_core_skills": missing_core,
            "missing_recommended_skills": missing_rec[:4],
            "match_percentage": match_score,
            "readiness_level": readiness,
            "recommendation": recommendation,
        }
