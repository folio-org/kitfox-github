import json
import os
import fnmatch
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Iterable, Callable

import boto3

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.github_client import GitHubClient
from common.workflow_trigger import WorkflowTrigger


logger = logging.getLogger()
logger.setLevel(logging.INFO)

_s3 = boto3.client("s3")


# =============================
# Models
# =============================

@dataclass(frozen=True)
class RepoInfo:
    owner: str
    name: str


@dataclass(frozen=True)
class NormalizedEvent:
    event_type: str
    action: str
    delivery_id: str
    repo: RepoInfo

    head_branch: str = ""
    base_branch: str = ""
    head_sha: str = ""
    base_sha: str = ""

    pr_number: str = ""
    merged: str = "false"
    is_merge_group: str = "false"

    event_id: str = ""
    check_suite_id: str = ""

    changed_files: Optional[List[str]] = None


# =============================
# Config loading
# =============================

def load_config_from_s3(bucket: Optional[str], key: Optional[str]) -> Dict[str, Any]:
    if not bucket or not key:
        logger.error("CONFIG_BUCKET_NAME or CONFIG_FILE_KEY missing")
        return {}

    try:
        obj = _s3.get_object(Bucket=bucket, Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception as e:
        logger.error("Failed to load config from S3: %s", e, exc_info=True)
        return {}


# =============================
# Utilities
# =============================

def _strip_ref(ref: str) -> str:
    return (ref or "").replace("refs/heads/", "")

def _match(value: str, pattern: str) -> bool:
    return fnmatch.fnmatch(value or "", pattern or "")

def _any_match(value: str, patterns: Iterable[str]) -> bool:
    return any(_match(value, p) for p in patterns)

def _substitute(value: Any, variables: Dict[str, str]) -> Any:
    if isinstance(value, str):
        for k, v in variables.items():
            value = value.replace(f"{{{k}}}", v)
        return value
    if isinstance(value, dict):
        return {k: _substitute(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute(v, variables) for v in value]
    return value


# =============================
# Push changed files
# =============================

def get_changed_files_from_push(payload: Dict[str, Any]) -> List[str]:
    changed = set()
    for commit in payload.get("commits", []):
        changed.update(commit.get("added", []))
        changed.update(commit.get("modified", []))
        changed.update(commit.get("removed", []))
    return list(changed)

def matches_file_patterns(changed_files: List[str], patterns: List[str]) -> bool:
    if not patterns:
        return True
    return any(fnmatch.fnmatch(f, p) for f in changed_files for p in patterns)


# =============================
# Event normalization (per event type)
# =============================

def _normalize_push(
        event_type: str,
        action: str,
        delivery_id: str,
        repo: RepoInfo,
        payload: Dict[str, Any],
) -> NormalizedEvent:
    return NormalizedEvent(
        event_type=event_type,
        action=action,
        delivery_id=delivery_id,
        repo=repo,
        head_branch=_strip_ref(payload.get("ref", "")),
        head_sha=payload.get("after", ""),
        changed_files=get_changed_files_from_push(payload),
        event_id="",
    )


def _normalize_merge_group(
        event_type: str,
        action: str,
        delivery_id: str,
        repo: RepoInfo,
        payload: Dict[str, Any],
) -> NormalizedEvent:
    mg = payload.get("merge_group", {}) or {}
    mg_id = str(mg.get("id", "") or "")
    return NormalizedEvent(
        event_type=event_type,
        action=action,
        delivery_id=delivery_id,
        repo=repo,
        head_branch=_strip_ref(mg.get("head_ref", "")),
        base_branch=_strip_ref(mg.get("base_ref", "")),
        head_sha=mg.get("head_sha", ""),
        base_sha=mg.get("base_sha", ""),
        is_merge_group="true",
        event_id=mg_id,
        check_suite_id=mg_id,
    )


def _normalize_pull_request(
        event_type: str,
        action: str,
        delivery_id: str,
        repo: RepoInfo,
        payload: Dict[str, Any],
) -> NormalizedEvent:
    pr = payload.get("pull_request", {}) or {}
    pr_id = str(pr.get("id", "") or "")
    pr_head = pr.get("head") or {}
    pr_base = pr.get("base") or {}

    return NormalizedEvent(
        event_type=event_type,
        action=action,
        delivery_id=delivery_id,
        repo=repo,
        head_branch=pr_head.get("ref", "") or "",
        base_branch=pr_base.get("ref", "") or "",
        head_sha=pr_head.get("sha", "") or "",
        base_sha=pr_base.get("sha", "") or "",
        pr_number=str(pr.get("number", "") or ""),
        merged=str(bool(pr.get("merged", False))).lower(),
        event_id=pr_id,
        check_suite_id="",
    )


def _normalize_check(
        event_type: str,
        action: str,
        delivery_id: str,
        repo: RepoInfo,
        payload: Dict[str, Any],
) -> NormalizedEvent:
    obj = payload.get(event_type, {}) or {}
    cs_id = str(obj.get("id", "") or "")

    prs = obj.get("pull_requests", []) or []
    pr0 = prs[0] if prs else {}
    pr0_base = (pr0.get("base") or {})

    return NormalizedEvent(
        event_type=event_type,
        action=action,
        delivery_id=delivery_id,
        repo=repo,
        head_branch=obj.get("head_branch", "") or "",
        head_sha=obj.get("head_sha", "") or "",
        base_branch=pr0_base.get("ref", "") or "",
        base_sha=pr0_base.get("sha", "") or "",
        pr_number=str(pr0.get("number", "") or ""),
        event_id=cs_id,
        check_suite_id=cs_id,
    )


_EVENT_NORMALIZERS: Dict[str, Callable[[str, str, str, RepoInfo, Dict[str, Any]], NormalizedEvent]] = {
    "push": _normalize_push,
    "merge_group": _normalize_merge_group,
    "pull_request": _normalize_pull_request,
    "check_suite": _normalize_check,
    "check_run": _normalize_check,
}


def normalize_event(message: Dict[str, Any]) -> NormalizedEvent:
    event_type = message.get("event_type", "") or ""
    action = message.get("action", "") or ""
    delivery_id = message.get("delivery_id", "") or ""
    payload = message.get("payload") or {}

    repo_obj = payload.get("repository") or {}
    owner = (repo_obj.get("owner") or {}).get("login") or ""
    name = repo_obj.get("name") or ""
    repo = RepoInfo(owner=owner, name=name)

    fn = _EVENT_NORMALIZERS.get(event_type)
    if fn:
        return fn(event_type, action, delivery_id, repo, payload)

    return NormalizedEvent(
        event_type=event_type,
        action=action,
        delivery_id=delivery_id,
        repo=repo,
    )


# =============================
# Branch matching (strict)
# =============================

def _primary_branch_for_simple_match(ev: NormalizedEvent) -> str:
    """
    For non-dict branch configs (string/list), pick ONE deterministic branch.
    This avoids the ambiguous 'head or base' fallback.
    """
    if ev.event_type == "pull_request":
        return ev.base_branch
    return ev.head_branch


def branch_matches_for_mapping(ev: NormalizedEvent, branches_cfg: Any) -> bool:
    """
    branches_cfg can be:
      - "*" / None
      - str
      - list[str]
      - dict: {"base":[...], "head":[...]} (structured constraints)
    Dict is NEVER a wildcard.
    """
    if branches_cfg == "*" or branches_cfg is None:
        return True

    if isinstance(branches_cfg, (str, list)):
        branch = _primary_branch_for_simple_match(ev)
        if isinstance(branches_cfg, str):
            return _match(branch, branches_cfg)
        return _any_match(branch, branches_cfg)

    if isinstance(branches_cfg, dict):
        if ev.event_type == "push":
            logger.warning("Branch dict is not supported for push events")
            return False

        base_patterns = branches_cfg.get("base")
        head_patterns = branches_cfg.get("head")

        if not base_patterns and not head_patterns:
            logger.warning("Empty branch dict in config")
            return False

        if base_patterns and not _any_match(ev.base_branch, base_patterns):
            return False
        if head_patterns and not _any_match(ev.head_branch, head_patterns):
            return False

        return True

    logger.warning("Unsupported branches config type: %s", type(branches_cfg))
    return False


# =============================
# Workflow matching
# =============================

def find_matching_workflows(ev: NormalizedEvent, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    workflows: List[Dict[str, Any]] = []

    for mapping in config.get("event_mappings", []):
        if mapping.get("event_type") != ev.event_type:
            continue

        actions = mapping.get("actions")
        if actions and ev.action not in actions:
            continue

        for repo_pattern in mapping.get("repository_patterns", []):
            if not _match(ev.repo.owner, repo_pattern.get("owner", "*")):
                continue
            if not _match(ev.repo.name, repo_pattern.get("repository", "*")):
                continue

            if not branch_matches_for_mapping(ev, repo_pattern.get("branches", "*")):
                continue

            if ev.event_type == "push" and ev.changed_files is not None:
                if not matches_file_patterns(ev.changed_files, repo_pattern.get("file_patterns", [])):
                    continue

            workflows.extend(repo_pattern.get("workflows", []))

    return workflows


# =============================
# Lambda handler
# =============================

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("Processing %d SQS records", len(event.get("Records", [])))

    config = load_config_from_s3(
        os.environ.get("CONFIG_BUCKET_NAME"),
        os.environ.get("CONFIG_FILE_KEY", "github_events_config.json"),
    )
    if not config:
        return {"statusCode": 500, "body": json.dumps({"error": "Config not found"})}

    fail_on_error = str(os.environ.get("FAIL_ON_ERROR", "false")).lower() == "true"

    github_client = GitHubClient()
    workflow_trigger = WorkflowTrigger(github_client)

    processed = 0
    errors = 0

    for record in event.get("Records", []):
        try:
            ev = normalize_event(json.loads(record.get("body", "{}")))
            workflows = find_matching_workflows(ev, config)

            if not workflows:
                processed += 1
                continue

            vars_ = {
                "owner": ev.repo.owner,
                "repository": ev.repo.name,
                "head_sha": ev.head_sha,
                "head_branch": ev.head_branch,
                "base_branch": ev.base_branch,
                "base_sha": ev.base_sha,
                "pr_number": ev.pr_number,
                "merged": ev.merged,
                "is_merge_group": ev.is_merge_group,
                "event_id": ev.event_id,
                "check_suite_id": ev.check_suite_id,
            }

            for wf in workflows:
                try:
                    rendered = _substitute(wf, vars_)
                    workflow_trigger.trigger_workflow(
                        owner=rendered["owner"],
                        repo=rendered["repository"],
                        workflow_file=rendered["workflow_file"],
                        ref=rendered.get("ref", "main"),
                        inputs=rendered.get("inputs", {}),
                    )
                except Exception:
                    errors += 1
                    logger.exception("Workflow trigger error")

            processed += 1

        except Exception:
            errors += 1
            logger.exception("Error processing record")

    if errors and fail_on_error:
        raise RuntimeError(f"Processing completed with {errors} errors (FAIL_ON_ERROR=true)")

    return {
        "statusCode": 200,
        "body": json.dumps({"processed": processed, "errors": errors}),
    }
