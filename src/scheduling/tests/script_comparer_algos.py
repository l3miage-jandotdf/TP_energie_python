import os
import time
import pandas as pd
from typing import Tuple, Type

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.optim.constructive import Greedy, NonDeterminist
from src.scheduling.optim.local_search import FirstNeighborLocalSearch, BestNeighborLocalSearch
from src.scheduling.optim.neighborhoods import ReassignOneOperation, SwapOperationsOnOneMachine


# --- Configuration ---
DATA_FOLDER = "./data" # Assuming 'data' folder is in the same directory as this script
INSTANCES_TO_TEST = ["jsp2", "jsp5", "jsp10", "jsp20", "jsp50", "jsp100"] # Select representative instances
NUM_RUNS_NON_DETERMINISTIC = 10 # Number of runs for NonDeterminist and initial solutions for Local Search
MAX_LS_ITERATIONS = 100 # Max iterations for local search
NO_IMPROVEMENT_LIMIT = 20 # Stop criterion for BestNeighborLocalSearch

# --- Helper Function for Algorithm Execution ---
def run_algorithm(algo_class: Type, instance: Instance, num_runs: int = 1, **kwargs) -> Tuple[float, float]:
    """
    Runs an algorithm multiple times and returns the best objective and average time.
    """
    best_objective = float('inf')
    total_time = 0.0

    print(f"  Running {algo_class.__name__} for {num_runs} times...")

    for i in range(num_runs):
        start_time = time.time()
        
        # Instantiate and run the heuristic
        # Special handling for Local Search to pass neighborhood classes
        if algo_class == FirstNeighborLocalSearch:
            heuristic = algo_class(kwargs.get("params", {}))
            solution = heuristic.run(instance, NonDeterminist, ReassignOneOperation, kwargs.get("params", {}))
        elif algo_class == BestNeighborLocalSearch:
            heuristic = algo_class(kwargs.get("params", {}))
            solution = heuristic.run(instance, NonDeterminist, [ReassignOneOperation, SwapOperationsOnOneMachine], kwargs.get("params", {}))
        else:
            heuristic = algo_class(kwargs.get("params", {}))
            solution = heuristic.run(instance, kwargs.get("params", {}))
        
        end_time = time.time()
        
        run_time = end_time - start_time
        total_time += run_time
        
        if solution.objective < best_objective:
            best_objective = solution.objective

    avg_time = total_time / num_runs
    return best_objective, avg_time

# --- Main Comparison Script ---
def main():
    results = []

    print("Starting algorithm comparison...")

    for instance_name in INSTANCES_TO_TEST:
        instance_path = os.path.join(DATA_FOLDER, instance_name)
        ops_file = os.path.join(instance_path, f"{instance_name}_op.csv")
        mach_file = os.path.join(instance_path, f"{instance_name}_mach.csv")

        if not os.path.exists(ops_file) or not os.path.exists(mach_file):
            print(f"  Skipping instance {instance_name}: files not found.")
            continue

        print(f"\n--- Processing instance: {instance_name} ---")
        instance = Instance.from_file(instance_path)

        # 1. Greedy Algorithm
        greedy_best_obj, greedy_avg_time = run_algorithm(Greedy, instance, num_runs=1) # Greedy is deterministic, so 1 run
        results.append({
            "Instance": instance_name,
            "Algorithm": "Greedy",
            "Best Objective": greedy_best_obj,
            "Average Time (s)": greedy_avg_time
        })

        # 2. NonDeterminist Algorithm
        nondeterminist_params = {"seed": None} # None means random each time
        nondeterminist_best_obj, nondeterminist_avg_time = run_algorithm(NonDeterminist, instance, num_runs=NUM_RUNS_NON_DETERMINISTIC, params=nondeterminist_params)
        results.append({
            "Instance": instance_name,
            "Algorithm": f"NonDeterminist (best of {NUM_RUNS_NON_DETERMINISTIC})",
            "Best Objective": nondeterminist_best_obj,
            "Average Time (s)": nondeterminist_avg_time
        })

        # 3. FirstNeighborLocalSearch
        fnls_params = {"max_iterations": MAX_LS_ITERATIONS, "seed": None} # Initial NonDeterminist will be random
        fnls_best_obj, fnls_avg_time = run_algorithm(FirstNeighborLocalSearch, instance, num_runs=NUM_RUNS_NON_DETERMINISTIC, params=fnls_params)
        results.append({
            "Instance": instance_name,
            "Algorithm": f"FirstNeighborLS (best of {NUM_RUNS_NON_DETERMINISTIC} initializations)",
            "Best Objective": fnls_best_obj,
            "Average Time (s)": fnls_avg_time
        })

        # 4. BestNeighborLocalSearch
        bnls_params = {"max_iterations": MAX_LS_ITERATIONS, "no_improvement_limit": NO_IMPROVEMENT_LIMIT, "seed": None}
        bnls_best_obj, bnls_avg_time = run_algorithm(BestNeighborLocalSearch, instance, num_runs=NUM_RUNS_NON_DETERMINISTIC, params=bnls_params)
        results.append({
            "Instance": instance_name,
            "Algorithm": f"BestNeighborLS (best of {NUM_RUNS_NON_DETERMINISTIC} initializations)",
            "Best Objective": bnls_best_obj,
            "Average Time (s)": bnls_avg_time
        })

    # Convert results to a pandas DataFrame for better visualization
    df_results = pd.DataFrame(results)
    print("\n--- Comparison Results ---")
    print(df_results.to_markdown(index=False))

    # Optional: Save results to CSV
    df_results.to_csv("algorithm_comparison_results.csv", index=False)
    print("\nResults saved to algorithm_comparison_results.csv")


if __name__ == "__main__":
    main()