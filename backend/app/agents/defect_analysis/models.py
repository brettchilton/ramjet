from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID

# Cost-related models
class DefectCostBreakdown(BaseModel):
    materials: float = Field(description="Material costs")
    labor: float = Field(description="Labor costs")
    equipment: float = Field(description="Equipment costs")
    
class DefectPricingFactors(BaseModel):
    complexity: str = Field(description="Complexity level: low, medium, high")
    access_difficulty: str = Field(description="Access difficulty: easy, moderate, difficult")
    
class LocationFactors(BaseModel):
    region: str = Field(description="Region/city name")
    postcode: str = Field(description="Postal code")

# Main defect analysis result
class DefectAnalysisResult(BaseModel):
    """Result from the defect analysis and costing workflow"""
    
    defect_id: UUID = Field(description="Defect UUID from database")
    
    # Core defect information (from analysis agent)
    defect_category: str = Field(description="High Risk, Major Defect, or Minor Defect")
    defect_type: str = Field(description="Standardized defect type")
    description: str = Field(description="Detailed defect description")
    rectification_works: str = Field(description="Recommended remediation method")
    rectification_type: str = Field(description="Repair, Replace, Install, etc.")
    priority: str = Field(description="Urgent-immediate, Within 12 months, etc.")
    
    # Cost estimation (from costing agent)
    cost_estimate: float = Field(description="Total estimated cost")
    cost_breakdown: DefectCostBreakdown
    cost_reasoning: str = Field(description="Explanation of pricing approach")
    pricing_factors: DefectPricingFactors
    cost_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in pricing (0-1)")
    
    # Location-based pricing
    location_factors: LocationFactors

class DefectAnalysisWorkflowResult(BaseModel):
    """Final output from the complete defect analysis workflow"""
    
    project_id: UUID
    building_id: UUID
    building_address: str
    
    analyzed_defects: List[DefectAnalysisResult]
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "building_id": "456e7890-e89b-12d3-a456-426614174000",
                "building_address": "123 Main St, Geelong VIC 3220",
                "analyzed_defects": [
                    {
                        "defect_id": "789e0123-e89b-12d3-a456-426614174000",
                        "defect_category": "Major Defect",
                        "defect_type": "Damaged downpipe causing discharge against building",
                        "description": "Rusted gutter section with damaged downpipe",
                        "rectification_works": "Replace damaged section of downpipe",
                        "rectification_type": "Replace",
                        "priority": "Within 12 months",
                        "cost_estimate": 395.00,
                        "cost_breakdown": {
                            "materials": 150,
                            "labor": 180,
                            "equipment": 65
                        },
                        "cost_reasoning": "Based on standard downpipe replacement",
                        "pricing_factors": {
                            "complexity": "medium",
                            "access_difficulty": "moderate"
                        },
                        "cost_confidence": 0.85,
                        "location_factors": {
                            "region": "Geelong",
                            "postcode": "3220"
                        }
                    }
                ]
            }
        }
