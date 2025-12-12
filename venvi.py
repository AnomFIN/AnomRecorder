#!/usr/bin/env python3
"""
Why this design: single entry point to provision an isolated .venv, install dependencies,
optionally wire in Node services, and launch AnomRecorder in a repeatable way.
- Functional helpers keep side-effects at the edge.
- Structured logs make automation and troubleshooting predictable.
- Guardrails ensure Python version/paths are validated before any install or launch.

AnomFIN — the neural network of innovation.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
MINIMUM_PYTHON = (3, 9)


@dataclass(frozen=True)
class VenvPaths:
    project_root: Path
    venv_dir: Path
    python: Path
    pip: Path
    bin_dir: Path
    npm_command: str


def log(event: str, **extra: object) -> None:
    payload = {"event": event, **extra}
    print(json.dumps(payload, ensure_ascii=False))


def ensure_python_version(minimum: tuple[int, int]) -> None:
    if sys.version_info < minimum:
        message = f"Python {minimum[0]}.{minimum[1]} or newer required; found {sys.version_info.major}.{sys.version_info.minor}."
        log("python.version.unsupported", message=message)
        raise SystemExit(message)
    log("python.version.ok", version=f"{sys.version_info.major}.{sys.version_info.minor}")


def resolve_paths(project_root: Path, venv_dir: Path | None = None, platform_os: str | None = None) -> VenvPaths:
    """Resolve venv-related paths with explicit platform awareness.

    platform_os can be overridden for testing; defaults to the current OS.
    """

    platform = platform_os or os.name
    venv_root = venv_dir or project_root / ".venv"
    bin_folder = venv_root / ("Scripts" if platform == "nt" else "bin")
    npm_executable = "npm.cmd" if platform == "nt" else "npm"
    python_executable = "python.exe" if platform == "nt" else "python"
    pip_executable = "pip.exe" if platform == "nt" else "pip"
    return VenvPaths(
        project_root=project_root,
        venv_dir=venv_root,
        python=bin_folder / python_executable,
        pip=bin_folder / pip_executable,
        bin_dir=bin_folder,
        npm_command=npm_executable,
    )


def with_venv_env(paths: VenvPaths) -> Mapping[str, str]:
    env = os.environ.copy()
    path_prefix = str(paths.bin_dir)
    env_path = env.get("PATH", "")
    env["PATH"] = path_prefix + os.pathsep + env_path
    env.setdefault("VIRTUAL_ENV", str(paths.venv_dir))
    return env


def run_command(command: Iterable[str], *, cwd: Path | None = None, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command_list = [str(part) for part in command]
    log("command.run", cmd=" ".join(command_list), cwd=str(cwd) if cwd else None)
    completed = subprocess.run(command_list, cwd=cwd, env=env, text=True, capture_output=True)
    if completed.returncode != 0:
        log(
            "command.error",
            cmd=" ".join(command_list),
            returncode=completed.returncode,
            stdout=completed.stdout.strip(),
            stderr=completed.stderr.strip(),
        )
        raise RuntimeError(f"Command failed: {' '.join(command_list)}")
    if completed.stdout.strip():
        log("command.stdout", output=completed.stdout.strip())
    if completed.stderr.strip():
        log("command.stderr", output=completed.stderr.strip())
    return completed


def ensure_virtualenv(paths: VenvPaths) -> None:
    if paths.python.exists():
        log("venv.exists", path=str(paths.venv_dir))
        return
    log("venv.create", path=str(paths.venv_dir))
    run_command([sys.executable, "-m", "venv", str(paths.venv_dir)], cwd=paths.project_root)


def install_python_dependencies(paths: VenvPaths, requirements_file: Path = DEFAULT_REQUIREMENTS, upgrade_tools: bool = True) -> None:
    if not requirements_file.exists():
        message = f"Requirements file not found: {requirements_file}"
        log("deps.missing", message=message)
        raise FileNotFoundError(message)
    env = with_venv_env(paths)
    if upgrade_tools:
        log("deps.pip.upgrade")
        run_command([paths.python, "-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools"], env=env)
    log("deps.install", requirements=str(requirements_file))
    run_command([paths.python, "-m", "pip", "install", "-r", str(requirements_file)], env=env)


def run_tests(paths: VenvPaths, extra_args: list[str] | None = None) -> None:
    args = extra_args or []
    env = with_venv_env(paths)
    pytest_cmd = [paths.python, "-m", "pytest", *args]
    log("tests.start")
    run_command(pytest_cmd, cwd=paths.project_root, env=env)


def run_node_service(paths: VenvPaths, script: str = "start") -> bool:
    package_json = paths.project_root / "package.json"
    if not package_json.exists():
        log("npm.skip", reason="package.json not found")
        return False
    env = with_venv_env(paths)
    log("npm.install")
    run_command([paths.npm_command, "install"], cwd=paths.project_root, env=env)
    log("npm.start", script=script)
    run_command([paths.npm_command, "run", script], cwd=paths.project_root, env=env)
    return True


def launch_app(paths: VenvPaths, entrypoint: str = "src.index") -> None:
    env = with_venv_env(paths)
    log("app.launch", entrypoint=entrypoint)
    command = [paths.python, "-m", entrypoint]
    run_command(command, cwd=paths.project_root, env=env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AnomRecorder inside a managed .venv.")
    parser.add_argument("action", choices=["run", "setup", "test"], default="run", nargs="?", help="What to execute.")
    parser.add_argument("--with-npm", dest="with_npm", action="store_true", help="Install and start npm service if package.json exists.")
    parser.add_argument("--skip-tests", dest="skip_tests", action="store_true", help="Skip pytest execution before launch.")
    parser.add_argument("--entrypoint", dest="entrypoint", default="src.index", help="Python module entrypoint to run.")
    parser.add_argument("--requirements", dest="requirements", default=str(DEFAULT_REQUIREMENTS), help="Requirements file path.")
    parser.add_argument("--pytest-args", dest="pytest_args", nargs=argparse.REMAINDER, help="Extra args forwarded to pytest.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_python_version(MINIMUM_PYTHON)
    paths = resolve_paths(PROJECT_ROOT)
    ensure_virtualenv(paths)
    install_python_dependencies(paths, Path(args.requirements))

    if args.action == "test":
        run_tests(paths, args.pytest_args or [])
        return 0

    if not args.skip_tests:
        run_tests(paths, args.pytest_args or [])

    if args.with_npm:
        run_node_service(paths)

    if args.action == "setup":
        log("setup.complete")
        return 0

    launch_app(paths, args.entrypoint)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
