from pathlib import Path

import venvi


def test_resolve_paths_defaults(tmp_path):
    project_root = tmp_path
    paths = venvi.resolve_paths(project_root)
    assert paths.project_root == project_root
    assert paths.venv_dir == project_root / ".venv"
    assert paths.python.parent == paths.bin_dir
    assert paths.pip.parent == paths.bin_dir


def test_resolve_paths_windows_names(tmp_path):
    project_root = tmp_path
    paths = venvi.resolve_paths(project_root, platform_os="nt")
    assert paths.bin_dir.name == "Scripts"
    assert paths.python.name == "python.exe"
    assert paths.pip.name == "pip.exe"
    assert paths.npm_command == "npm.cmd"


def test_with_venv_env_prefixes_path(tmp_path):
    paths = venvi.resolve_paths(tmp_path)
    env = venvi.with_venv_env(paths)
    assert env["PATH"].split(venvi.os.pathsep)[0] == str(paths.bin_dir)
    assert env["VIRTUAL_ENV"] == str(paths.venv_dir)


def test_virtualenv_cycle_and_dependency_install(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    requirements = project_root / "requirements.txt"
    requirements.write_text("")
    paths = venvi.resolve_paths(project_root)

    venvi.ensure_virtualenv(paths)
    assert paths.python.exists()

    venvi.install_python_dependencies(paths, requirements, upgrade_tools=False)

    env = venvi.with_venv_env(paths)
    assert Path(env["PATH"].split(venvi.os.pathsep)[0]).exists()
    assert env["VIRTUAL_ENV"] == str(paths.venv_dir)


def test_run_node_service_skips_when_missing_package(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    paths = venvi.resolve_paths(project_root)
    venvi.ensure_virtualenv(paths)
    assert venvi.run_node_service(paths) is False
