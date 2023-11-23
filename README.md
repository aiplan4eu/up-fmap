# FMAP Unified Planning integrator 

The aim of this project is to make the [FMAP](https://bitbucket.org/altorler/fmap/src/master/) planning engine available in the [unified_planning
library](https://github.com/aiplan4eu/unified-planning) by the [AIPlan4EU project](https://www.aiplan4eu-project.eu/).

FMAP uses a distributed heuristic search strategy. Each planning agent in the platform features an embedded search engine based on a forward partial-order planning scheme
FMAP leverages a forward-chaining partial-order planner (POP) that allows agents to plan their actions in parallel whenever possible, which largely improves the quality of the resulting solution plans. Moreover, the forward-chaining approach relies on the frontier state (state that results from executing the actions of a node) to compute accurate state-based estimates.

## Installation

We recommend the installation from PyPi because it has pre-built wheels for all common operating systems.

### Installation from Python Package Index PyPi

To automatically get a version that works with your version of the unified planning framework, you can list it as a solver in the pip installation of ```unified_planning```:

```
pip install unified-planning[fmap]
```

If you need several solvers, you can list them all within the brackets.

You can also install the FMAP integration separately (in case the current version of unified_planning does not include FMAP or you want to add it later to your unified planning installation). With

```
pip install up-fmap
```

you get the latest version. If you need an older version, you can install it with:

```
pip install up-fmap==<version number>
```
## Usage

### Solving a planning problem

You can use fmap to solve a Multi-Agent problem. It allows the specification of a specific heuristic function used to evaluate the quality of the plans. The name of the custom parameter is heuristic and the following values are supported:

- 0 - FF heuristic: guides the search through the well-known h_FF heuristic function. This option is available for single-agent planning tasks only.
- 1 - DTG heuristic: evaluates plans via the heuristic h_DTG.
- 2 - default option - DTG + Landmarks: this option applies the multi-heuristic search scheme of the MH-FMAP solver by combining the h_DTG and h_Land heuristics to guide the search.
- 3 - Inc. DTG + Landmarks: incremental multi-heuristic mode that makes use of h_DTG and h_Land.
You can for example call it as follows:

```
from unified_planning.shortcuts import *
from unified_planning.engines import PlanGenerationResultStatus

problem = MultiAgentProblem('myproblem')
# specify the problem (e.g. agents, agent public fluents, agent private fluents, environment fluents, initial state, agent actions, goal)
...

planner = OneshotPlanner(name="fmap")
result = planner.solve(problem)
if result.status == PlanGenerationResultStatus.SOLVED_SATISFICING:
    print(f'{Found a plan.\nThe plan is: {result.plan}')
else:
    print("No plan found.")
```
Notebooks:

[Multi-Agent Plan Simple Example](https://github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/09-multiagent-planning-simple.ipynb)

[Multi-Agent Plan Example](https://github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/10-multiagent-planning.ipynb)

## Planning approaches of UP supported
Multi-agent planning

## Default configuration
DTG + Landmarks: this option applies the multi-heuristic search scheme of the MH-FMAP solver (described in this [paper](https://ojs.aaai.org/index.php/ICAPS/article/view/13701)) by combining the h_DTG and h_Land heuristics to guide the search.

## Operative modes of UP currently supported
Oneshot planning [UP Documentation](https://unified-planning.readthedocs.io/en/latest/operation_modes.html#oneshotplanner)
