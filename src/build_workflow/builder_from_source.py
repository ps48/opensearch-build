# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

import os

from build_workflow.build_recorder import BuildRecorder
from build_workflow.builder import Builder
from git.git_repository import GitRepository
from paths.script_finder import ScriptFinder

"""
This class is responsible for executing the build for a component and passing the results to a build recorder.
It will notify the build recorder of build information such as repository and git ref, and any artifacts generated by the build.
Artifacts found in "<build root>/artifacts/<maven|plugins|libs|dist|core-plugins>" will be recognized and recorded.
"""


class BuilderFromSource(Builder):
    def checkout(self, work_dir: str) -> None:
        self.git_repo = GitRepository(
            self.component.repository,
            self.component.ref,
            os.path.join(work_dir, self.component.name),
            self.component.working_directory,
        )

    def build(self, build_recorder: BuildRecorder) -> None:
        build_script = ScriptFinder.find_build_script(self.target.name, self.component.name, self.git_repo.working_directory)

        build_command = " ".join(
            filter(
                None,
                [
                    "bash",
                    build_script,
                    f"-v {self.target.version}",
                    f"-p {self.target.platform}",
                    f"-a {self.target.architecture}",
                    f"-d {self.target.distribution}" if self.target.distribution else None,
                    f"-s {str(self.target.snapshot).lower()}",
                    f"-o {self.output_path}",
                ]
            )
        )

        self.git_repo.execute(build_command)
        build_recorder.record_component(self.component.name, self.git_repo)

    def export_artifacts(self, build_recorder: BuildRecorder) -> None:
        artifacts_path = os.path.join(self.git_repo.working_directory, self.output_path)
        for artifact_type in ["maven", "dist", "plugins", "libs", "core-plugins"]:
            for dir, _, files in os.walk(os.path.join(artifacts_path, artifact_type)):
                for file_name in files:
                    absolute_path = os.path.join(dir, file_name)
                    relative_path = os.path.relpath(absolute_path, artifacts_path)
                    build_recorder.record_artifact(self.component.name, artifact_type, relative_path, absolute_path)
