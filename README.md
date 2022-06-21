# FMAP Unified Planning integrator 
This is the FMAP UP integrator. 
FMAP uses a distributed heuristic search strategy. Each planning agent in the platform features an embedded search engine based on a forward partial-order planning scheme
FMAP leverages a forward-chaining partial-order planner (POP) that allows agents to plan their actions in parallel whenever possible, which largely improves the quality of the resulting solution plans. Moreover, the forward-chaining approach relies on the frontier state (state that results from executing the actions of a node) to compute accurate state-based estimates.

## Installation
After cloning this repository run ```pip install up-fmap/```. 

FMAP will be downloaded from the public repository of FMAP.
FMAP, and therefore this integrator requires openjdk 17 installed on your machine.

The installation has been tested in Ubuntu 20.04.3 LTS.

## Planning approaches of UP supported
Multi-agent planning

## Default configuration
DTG + Landmarks: this option applies the multi-heuristic search scheme of the MH-FMAP solver (described in this [paper](https://ojs.aaai.org/index.php/ICAPS/article/view/13701)) by combining the h_DTG and h_Land heuristics to guide the search.

## Operative modes of UP currently supported
One shot planning (ongoing)
