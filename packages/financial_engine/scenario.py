from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Callable, Any
from packages.financial_engine.forecast import ForecastAssumption, ForecastResult

class ScenarioCase(BaseModel):
    name: Literal['BEAR', 'BASE', 'BULL'] = Field(description="Scenario identifier")
    description: str = Field(description="Qualitative description of the scenario rationale")
    assumptions: Dict[str, ForecastAssumption] = Field(description="Assumptions used in this scenario")
    forecast_result: Optional[ForecastResult] = Field(None, description="The resulting forecast for this scenario")
    valuation_result: Optional[Dict[str, Any]] = Field(None, description="The resulting valuation for this scenario")
    fair_value: Optional[float] = Field(None, description="The fair value output")
    warnings: List[str] = Field(default_factory=list, description="Any warnings generated")

class ScenarioSet(BaseModel):
    bear: ScenarioCase = Field(description="Bear case scenario")
    base: ScenarioCase = Field(description="Base case scenario")
    bull: ScenarioCase = Field(description="Bull case scenario")

class ScenarioEngine:
    """Engine for creating scenarios and sensitivity tables."""
    
    @staticmethod
    def create_scenario_set(bear_assumptions: Dict[str, ForecastAssumption], 
                            base_assumptions: Dict[str, ForecastAssumption], 
                            bull_assumptions: Dict[str, ForecastAssumption]) -> ScenarioSet:
        """Creates a ScenarioSet from explicit assumption dictionaries."""
        bear_case = ScenarioCase(name='BEAR', description="Bear Case", assumptions=bear_assumptions)
        base_case = ScenarioCase(name='BASE', description="Base Case", assumptions=base_assumptions)
        bull_case = ScenarioCase(name='BULL', description="Bull Case", assumptions=bull_assumptions)
        return ScenarioSet(bear=bear_case, base=base_case, bull=bull_case)

    @staticmethod
    def validate_scenario_consistency(scenario_set: ScenarioSet) -> List[str]:
        """Check that bear <= base <= bull for key metrics (growth, margins)."""
        warnings = []
        keys = set(scenario_set.base.assumptions.keys())
        
        # Common keys that usually follow bear < base < bull monotonically
        monotonic_keys = ['revenue_growth', 'loan_growth', 'margin', 'nim', 'terminal_growth']
        inverse_keys = ['cost_of_risk', 'tax_rate', 'cost_to_income'] # Where bear > base > bull
        
        for key in keys:
            if key in scenario_set.bear.assumptions and key in scenario_set.bull.assumptions:
                bear_val = scenario_set.bear.assumptions[key].value
                base_val = scenario_set.base.assumptions[key].value
                bull_val = scenario_set.bull.assumptions[key].value
                
                if key in monotonic_keys:
                    if not (bear_val <= base_val <= bull_val):
                        warnings.append(f"Inconsistent {key}: bear ({bear_val}) should be <= base ({base_val}) <= bull ({bull_val})")
                elif key in inverse_keys:
                    if not (bear_val >= base_val >= bull_val):
                        warnings.append(f"Inconsistent {key}: bear ({bear_val}) should be >= base ({base_val}) >= bull ({bull_val})")
                        
        return warnings

    @staticmethod
    def generate_sensitivity_table(base_assumptions: Dict[str, ForecastAssumption], 
                                   variable_name: str, 
                                   variable_range: List[float], 
                                   second_variable: Optional[str] = None, 
                                   second_range: Optional[List[float]] = None, 
                                   valuation_func: Callable[[Dict[str, ForecastAssumption]], float] = None) -> Dict[str, Any]:
        """
        Generates a 1D or 2D sensitivity table. 
        Requires a valuation function that takes a dict of ForecastAssumptions and returns a fair value (float).
        """
        if not valuation_func:
            raise ValueError("valuation_func must be provided to generate sensitivity table.")
            
        if not second_variable or not second_range:
            # 1D sensitivity table
            results = []
            for val in variable_range:
                test_assumptions = base_assumptions.copy()
                base_assumption_obj = test_assumptions[variable_name]
                test_assumptions[variable_name] = ForecastAssumption(
                    metric_name=base_assumption_obj.metric_name,
                    value=val,
                    source=f"Sensitivity Table Range",
                    rationale="Sensitivity variation"
                )
                fair_value = valuation_func(test_assumptions)
                results.append({"value": val, "fair_value": fair_value})
                
            return {
                "type": "1D",
                "variable": variable_name,
                "range": variable_range,
                "results": results
            }
        else:
            # 2D sensitivity table
            matrix = []
            for val1 in variable_range:
                row = []
                for val2 in second_range:
                    test_assumptions = base_assumptions.copy()
                    
                    base_assumption_obj1 = test_assumptions[variable_name]
                    test_assumptions[variable_name] = ForecastAssumption(
                        metric_name=base_assumption_obj1.metric_name,
                        value=val1,
                        source="Sensitivity Table Range",
                        rationale="Sensitivity variation"
                    )
                    
                    base_assumption_obj2 = test_assumptions[second_variable]
                    test_assumptions[second_variable] = ForecastAssumption(
                        metric_name=base_assumption_obj2.metric_name,
                        value=val2,
                        source="Sensitivity Table Range",
                        rationale="Sensitivity variation"
                    )
                    
                    fair_value = valuation_func(test_assumptions)
                    row.append(fair_value)
                matrix.append(row)
                
            return {
                "type": "2D",
                "row_variable": variable_name,
                "col_variable": second_variable,
                "row_range": variable_range,
                "col_range": second_range,
                "matrix": matrix
            }
