from pydantic import BaseModel, Field
from typing import List

class DataQualityDimension(BaseModel):
    dimension_name: str
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    explanation: str

class DataQualityScore(BaseModel):
    dimensions: List[DataQualityDimension]
    overall_score: float
    overall_explanation: str

def calculate_data_quality(source_quality: float, completeness: float, recency: float, consistency: float, extraction_confidence: float, market_completeness: float) -> DataQualityScore:
    dimensions = [
        DataQualityDimension(dimension_name="source_quality", score=source_quality, weight=0.2, explanation="Quality and reliability of the data source."),
        DataQualityDimension(dimension_name="completeness", score=completeness, weight=0.2, explanation="Extent to which all required data points are present."),
        DataQualityDimension(dimension_name="recency", score=recency, weight=0.15, explanation="Freshness of the data relative to the analysis date."),
        DataQualityDimension(dimension_name="consistency", score=consistency, weight=0.15, explanation="Internal consistency of the data (e.g. balance sheet balancing)."),
        DataQualityDimension(dimension_name="extraction_confidence", score=extraction_confidence, weight=0.15, explanation="Confidence level of data extraction processes."),
        DataQualityDimension(dimension_name="market_completeness", score=market_completeness, weight=0.15, explanation="Completeness of relevant market data (prices, volumes, macro).")
    ]
    
    total_weight = sum(d.weight for d in dimensions)
    overall_score = sum(d.score * (d.weight / total_weight) for d in dimensions)
    
    return DataQualityScore(
        dimensions=dimensions,
        overall_score=overall_score,
        overall_explanation=f"Overall data quality calculated via weighted average across {len(dimensions)} dimensions."
    )
