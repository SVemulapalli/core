from typing import Any, Callable

from zenbase.adaptors.base.evaluation_helper import BaseEvaluationHelper
from zenbase.optim.metric.types import CandidateEvalResult, CandidateEvaluator, IndividualEvalValue, OverallEvalValue
from zenbase.types import LMDemo, LMFunction
from zenbase.utils import pmap


class JSONEvaluationHelper(BaseEvaluationHelper):
    MetricEvaluator = Callable[[list[tuple[bool, Any]]], OverallEvalValue]

    @staticmethod
    def default_metric(batch_results: list[tuple[bool, Any]]) -> OverallEvalValue:
        avg_pass = sum(int(result["passed"]) for result in batch_results) / len(batch_results)
        return {"score": avg_pass}

    def get_evaluator(self, data: str):
        raise NotImplementedError("This method should be implemented by the parent class as it needs access to data")

    @staticmethod
    def _metric_evaluator_generator(
        *args,
        eval_function: Callable,
        data: list[LMDemo],
        eval_metrics: MetricEvaluator = default_metric,
        concurrency: int = 1,
        **kwargs,
    ) -> CandidateEvaluator:
        # TODO: Should remove and deprecate
        def evaluate_metric(function: LMFunction) -> CandidateEvalResult:
            individual_evals = []

            def run_and_evaluate(demo: LMDemo):
                nonlocal individual_evals

                response = function(demo.inputs)
                result = eval_function(
                    input=demo.inputs,
                    output=response,
                    ideal_output=demo.outputs,
                    *args,
                    **kwargs,
                )

                individual_evals.append(
                    IndividualEvalValue(
                        passed=result["passed"],
                        response=response,
                        demo=demo,
                    )
                )

                return result

            eval_results = pmap(
                run_and_evaluate,
                data,
                concurrency=concurrency,
            )

            return CandidateEvalResult(function, eval_metrics(eval_results), individual_evals=individual_evals)

        return evaluate_metric

    @classmethod
    def metric_evaluator(
        cls,
        eval_function: Callable,
        data: list[LMDemo],
        eval_metrics: MetricEvaluator = default_metric,
        concurrency: int = 1,
        threshold: float = 0.5,
    ) -> CandidateEvaluator:
        # TODO: Should remove and deprecate
        def evaluate_metric(function: LMFunction) -> CandidateEvalResult:
            individual_evals = []

            def run_and_evaluate(demo: LMDemo):
                nonlocal individual_evals

                response = function(demo.inputs)
                result = eval_function(
                    output=response,
                    ideal_output=demo.outputs,
                )

                individual_evals.append(
                    IndividualEvalValue(
                        passed=result["passed"],
                        response=response,
                        demo=demo,
                    )
                )

                return result

            eval_results = pmap(
                run_and_evaluate,
                data,
                concurrency=concurrency,
            )

            return CandidateEvalResult(function, eval_metrics(eval_results), individual_evals=individual_evals)

        return evaluate_metric
