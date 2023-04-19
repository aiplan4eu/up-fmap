import pkg_resources  # type: ignore
import unified_planning as up  # type: ignore
from unified_planning.model import ProblemKind  # type: ignore
from unified_planning.engines import Engine, Credits, LogMessage  # type: ignore
from unified_planning.engines.mixins import OneshotPlannerMixin  # type: ignore
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
import re
from unified_planning.plans.partial_order_plan import PartialOrderPlan
from collections import defaultdict

credits = Credits(
    "FMAP",
    "Alejandro Torreño, Oscar Sapena and Eva Onaindia",
    "altorler@upvnet.upv.es, osapena@dsic.upv.es",
    "https://bitbucket.org/altorler/fmap/src/master/",
    "GPL",
    "FMAP: A Platform for the Development of Distributed Multi-Agent Planning Systems.",
    "FMAP uses a distributed heuristic search strategy. Each planning agent in the platform features an embedded search engine based on a forward partial-order planning scheme. ",
)


class FMAPsolver(Engine, OneshotPlannerMixin):
    def __init__(
        self, search_algorithm: Optional[str] = None, heuristic: Optional[str] = None
    ):
        Engine.__init__(self)
        OneshotPlannerMixin.__init__(self)
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
        self, problem: MultiAgentProblem, domain_filename: str, problem_filename: str
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
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
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

    def _solve(
        self,
        problem: "up.model.AbstractProblem",
        callback: Optional[
            Callable[["up.engines.results.PlanGenerationResult"], None]
        ] = None,
        heuristic: Optional[
            Callable[["up.model.state.ROState"], Optional[float]]
        ] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        assert isinstance(problem, up.model.Problem) or isinstance(
            problem, up.model.multi_agent.MultiAgentProblem
        )
        plan = None
        logs: List["up.engines.results.LogMessage"] = []
        with tempfile.TemporaryDirectory() as tempdir:
            w = MAPDDLWriter(problem)
            domain_filename = os.path.join(tempdir, "domain_pddl/")
            problem_filename = os.path.join(tempdir, "problem_pddl/")
            plan_filename = os.path.join(tempdir, "plan.txt")
            plan_filename = "ma_pddl_" + plan_filename
            w.write_ma_domain(domain_filename)
            w.write_ma_problem(problem_filename)
            cmd = self._get_cmd_ma(problem, domain_filename, problem_filename)
            if heuristic is not None:
                cmd += ["-h", heuristic]
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

            f = open(plan_filename, "a+")
            pattern = re.compile(r"[Ee]rror|[Ee]xception")
            FAMP_error = False
            for line in proc_out:
                if pattern.search(line):
                    FAMP_error = True
                if not FAMP_error:
                    f.write(line + "\n")
            f.close()

            logs.append(up.engines.results.LogMessage(LogLevel.INFO, "".join(proc_out)))
            logs.append(
                up.engines.results.LogMessage(LogLevel.ERROR, "".join(proc_err))
            )

            if not FAMP_error:
                if os.path.isfile(plan_filename):
                    plan = self._plan_from_file(
                        problem, plan_filename, w.get_item_named
                    )
            else:
                plan = None

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

    def _plan_from_file(
        self,
        problem: "up.model.multi_agent.MultiAgentProblem",
        plan_filename: str,
        get_item_named: Callable[
            [str],
            Union[
                "up.model.Type",
                "up.model.Action",
                "up.model.Fluent",
                "up.model.Object",
                "up.model.Parameter",
                "up.model.Variable",
                "up.model.multi_agent.Agent",
            ],
        ],
    ) -> "up.plans.Plan":
        """
        Takes a problem, a filename and a map of renaming and returns the plan parsed from the file.

        :param problem: The up.model.problem.Problem instance for which the plan is generated.
        :param plan_filename: The path of the file in which the plan is written.
        :param get_item_named: A function that takes a name and returns the original up.model element instance
            linked to that renaming.
        :return: The up.plans.Plan corresponding to the parsed plan from the file
        """
        # ^(\d*).+\((\S*).+?(\S*).+?(.+(?=\)))
        dates_dict = defaultdict(list)
        adjacency_list = defaultdict(list)
        with open(plan_filename) as plan:
            for line in plan.readlines():
                line = line.lower()
                # match_line = re.match(r"^(\d*).+\((\S*).+?(\S*).+?(.+(?=\)))", line)
                match_line = re.match(r"^(\d*).+\((\S*)\s([^)\s]+)(?:\s(.+))?\)", line)
                if match_line:

                    timestamp = match_line.group(1)
                    action_name = match_line.group(2)
                    agent_name = match_line.group(3)
                    params_name = match_line.group(4)
                    if params_name:
                        params_name = params_name.split()
                    else:
                        params_name = []

                    action = get_item_named(action_name)
                    agent = get_item_named(agent_name)
                    assert isinstance(
                        action, up.model.Action
                    ), "Wrong plan or renaming."
                    parameters = []
                    for p in params_name:
                        obj = get_item_named(p)
                        assert isinstance(
                            obj, up.model.Object
                        ), "Wrong plan or renaming."
                        parameters.append(
                            problem.environment.expression_manager.ObjectExp(obj)
                        )
                    act_instance = up.plans.ActionInstance(
                        action, tuple(parameters), agent
                    )

                    dates_dict[timestamp].append(act_instance)

            dict_s = sorted(dates_dict.items(), key=lambda x: int(x[0]))

            for k, v in enumerate(dict_s):
                index = k + 1
                for action in v[1]:
                    if index < len(dates_dict):
                        next_action = dict_s[k + 1][1]
                        adjacency_list[action].extend(next_action)
                    elif len(dates_dict) == 1:
                        adjacency_list[action] = []

        return up.plans.PartialOrderPlan(adjacency_list)


env = up.environment.get_environment()
env.factory.add_engine("fmap", __name__, "FMAPsolver")
