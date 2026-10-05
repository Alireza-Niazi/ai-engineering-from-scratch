#!/usr/bin/env python3
"""Regression checks for the beginner lesson workflow."""

from pathlib import Path
import re
import shlex
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "run-lessons.yml"


class RunLessonsWorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.verify, cls.lessons = cls.workflow.split("  run-lessons:\n")

    def test_all_requested_triggers_are_unfiltered(self) -> None:
        triggers = self.workflow.split("on:\n", 1)[1].split("permissions:", 1)[0]
        self.assertEqual(
            triggers.strip(),
            "push:\n    branches: [main]\n  pull_request:\n  workflow_dispatch:",
        )

    def test_jobs_use_python_311_and_read_only_checkout(self) -> None:
        self.assertIn("permissions:\n  contents: read\n", self.workflow)
        for job in (self.verify, self.lessons):
            with self.subTest(job=job):
                self.assertIn("runs-on: ubuntu-latest", job)
                self.assertIn("python-version: '3.11'", job)
                self.assertIn("persist-credentials: false", job)
                self.assertRegex(job, r"timeout-minutes: \d+")
                self.assertEqual(len(re.findall(r"uses: \S+@[a-f0-9]{40}", job)), 2)

    def test_lessons_wait_for_dependency_free_preflight(self) -> None:
        self.assertIn("needs: verify-env\n", self.lessons)
        self.assertNotIn("pip install", self.verify)
        self.assertIn(
            "run: python3 phases/00-setup-and-tooling/01-dev-environment/"
            "code/verify.py --route beginner",
            self.verify,
        )
        install = next(
            line.strip() for line in self.lessons.splitlines() if "pip install" in line
        )
        self.assertEqual(
            install, "run: python3 -m pip install numpy==2.2.6 matplotlib==3.10.3"
        )

    def test_lesson_commands_exist_and_output_is_not_redirected(self) -> None:
        self.assertIn(
            "run: python3 phases/01-math-foundations/"
            "01-linear-algebra-intuition/code/vectors.py",
            self.lessons,
        )
        commands = re.findall(r"^\s+run: (python3 phases/.+)$", self.workflow, re.M)
        self.assertEqual(len(commands), 2)
        for command in commands:
            with self.subTest(command=command):
                args = shlex.split(command)
                self.assertTrue((ROOT / args[1]).is_file())
                self.assertNotRegex(command, r"[>|&]")


if __name__ == "__main__":
    unittest.main()
