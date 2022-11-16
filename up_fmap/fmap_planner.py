import pkg_resources  # type: ignore
import unified_planning as up  # type: ignore
from unified_planning.model import ProblemKind  # type: ignore
from unified_planning.engines import PDDLPlanner, Credits, LogMessage  # type: ignore
from typing import Callable, Dict, IO, List, Optional, Set, Union, cast  # type: ignore
from unified_planning.io.ma_pddl_writer import MAPDDLWriter  # type: ignore
import tempfile
import os
import subprocess
import sys
import asyncio
from unified_planning.engines.pddl_planner import (
    run_command_asyncio,
    run_command_posix_select,
    USE_ASYNCIO_ON_UNIX,
)  # type: ignore
from unified_planning.engines.results import (
    LogLevel,
    LogMessage,
    PlanGenerationResult,
    PlanGenerationResultStatus,
)  # type: ignore
from unified_planning.model.multi_agent import MultiAgentProblem  # type: ignore

credits = Credits(
    "FMAP",
    "Alejandro Torreño, Oscar Sapena and Eva Onaindia",
    "altorler@upvnet.upv.es, osapena@dsic.upv.es",
    "https://bitbucket.org/altorler/fmap/src/master/",
    "GPL",
    "FMAP: A Platform for the Development of Distributed Multi-Agent Planning Systems.",
    "FMAP uses a distributed heuristic search strategy. Each planning agent in the platform features an embedded search engine based on a forward partial-order planning scheme. ",
)


class FMAPsolver(PDDLPlanner):
    def __init__(
        self, search_algorithm: Optional[str] = None, heuristic: Optional[str] = None
    ):
        super().__init__(needs_requirements=False)
        self.search_algorithm = search_algorithm
        self.heuristic = heuristic

    @property
    def name(self) -> str:
        return "FMAP"

    def _manage_parameters(self, command):
        if self.search_algorithm is not None:
            command += ["-s", self.search_algorithm]
        if self.heuristic is not None:
            command += ["-h", self.heuristic]
        return command

    def _get_cmd_ma(
        self,
        problem: MultiAgentProblem,
        domain_filename: str,
        problem_filename: str,
        plan_filename: str,
    ):
        base_command = [
            "java",
            "-jar",
            pkg_resources.resource_filename("up_fmap", "FMAP/FMAP.jar"),
        ]
        directory = "ma_pddl_"
        for ag in problem.agents:
            base_command.extend(
                [
                    f"{ag.name}_type",
                    f"{directory}{domain_filename}{ag.name}_domain.pddl",
                ]
            )
            base_command.extend(
                [f"{directory}{problem_filename}{ag.name}_problem.pddl"]
            )
        return self._manage_parameters(base_command)

    def _result_status(
        self,
        problem: "up.model.multi_agent.MultiAgentProblem",
        plan: Optional["up.plans.Plan"],
        retval: int = 0,
        log_messages: Optional[List["LogMessage"]] = None,
    ) -> "PlanGenerationResultStatus":
        if retval != 0:
            return PlanGenerationResultStatus.INTERNAL_ERROR
        elif plan is None:
            return PlanGenerationResultStatus.UNSOLVABLE_PROVEN
        else:
            return PlanGenerationResultStatus.SOLVED_SATISFICING

    @staticmethod
    def supported_kind() -> "ProblemKind":
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED_MULTI_AGENT")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITY")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        return supported_kind

    @staticmethod
    def supports(problem_kind: "ProblemKind") -> bool:
        return problem_kind <= FMAPsolver.supported_kind()

    @staticmethod
    def get_credits(**kwargs) -> Optional["Credits"]:
        return credits

    def solve_ma(
        self,
        problem: "up.model.multi_agent.MultiAgentProblem",
        callback: Optional[
            Callable[["up.engines.results.PlanGenerationResult"], None]
        ] = None,
        heuristic: Optional[
            Callable[["up.model.state.ROState"], Optional[float]]
        ] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        assert isinstance(problem, up.model.multi_agent.MultiAgentProblem)
        w = MAPDDLWriter(problem)
        plan = None
        logs: List["up.engines.results.LogMessage"] = []
        with tempfile.TemporaryDirectory() as tempdir:
            domain_filename = os.path.join(tempdir, "domain.pddl/")
            problem_filename = os.path.join(tempdir, "problem.pddl/")
            plan_filename = os.path.join(tempdir, "plan.txt")
            w.write_ma_domain(domain_filename)
            w.write_ma_problem(problem_filename)
            cmd = self._get_cmd_ma(
                problem, domain_filename, problem_filename, plan_filename
            )
            if output_stream is None:
                # If we do not have an output stream to write to, we simply call
                # a subprocess and retrieve the final output and error with communicate
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                timeout_occurred: bool = False
                proc_out: List[str] = []
                proc_err: List[str] = []
                try:
                    out_err_bytes = process.communicate(timeout=timeout)
                    proc_out, proc_err = [[x.decode()] for x in out_err_bytes]
                except subprocess.TimeoutExpired:
                    timeout_occurred = True
                retval = process.returncode
            else:
                if sys.platform == "win32":
                    # On windows we have to use asyncio (does not work inside notebooks)
                    try:
                        loop = asyncio.ProactorEventLoop()
                        exec_res = loop.run_until_complete(
                            run_command_asyncio(
                                cmd, output_stream=output_stream, timeout=timeout
                            )
                        )
                    finally:
                        loop.close()
                else:
                    # On non-windows OSs, we can choose between asyncio and posix
                    # select (see comment on USE_ASYNCIO_ON_UNIX variable for details)
                    if USE_ASYNCIO_ON_UNIX:
                        exec_res = asyncio.run(
                            run_command_asyncio(
                                cmd, output_stream=output_stream, timeout=timeout
                            )
                        )
                    else:
                        exec_res = run_command_posix_select(
                            cmd, output_stream=output_stream, timeout=timeout
                        )
                timeout_occurred, (proc_out, proc_err), retval = exec_res

            logs.append(up.engines.results.LogMessage(LogLevel.INFO, "".join(proc_out)))
            logs.append(
                up.engines.results.LogMessage(LogLevel.ERROR, "".join(proc_err))
            )
            if os.path.isfile(plan_filename):
                plan = self._plan_from_file(problem, plan_filename, w.get_item_named)
            if timeout_occurred and retval != 0:
                return PlanGenerationResult(
                    PlanGenerationResultStatus.TIMEOUT,
                    plan=plan,
                    log_messages=logs,
                    engine_name=self.name,
                )
        status: PlanGenerationResultStatus = self._result_status(
            problem, plan, retval, logs
        )
        return PlanGenerationResult(
            status, plan, log_messages=logs, engine_name=self.name
        )
