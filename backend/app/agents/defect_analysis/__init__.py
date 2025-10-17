"""
Building Defect Analysis Agents

This module provides AI-powered analysis of building defects using a two-agent workflow:

1. DefectAnalysisAgent: Analyzes defect photos and provides detailed assessment
2. CostingAgent: Provides comprehensive cost estimates for remediation

Key Components:
- models.py: Pydantic models for structured data
- agents.py: Agent definitions and configurations  
- workflow.py: Main workflow orchestration
- example.py: Usage example

Usage:
    from app.agents.defect_analysis.workflow import analyze_building_defect
    
    result = await analyze_building_defect(
        photo1_path=Path("defect_closeup.jpg"),
        photo2_path=Path("defect_context.jpg"), 
        building_address="123 Main St, Melbourne VIC 3000"
    )
"""

from .workflow import DefectAnalysisWorkflow, analyze_building_defect
from .agent_definitions import defect_analysis_agent, costing_agent
from .models import (
    DefectAnalysisResult,
    DefectAnalysisWorkflowResult,
    DefectCostBreakdown,
    DefectPricingFactors,
    LocationFactors
)

__all__ = [
    'DefectAnalysisWorkflow',
    'analyze_building_defect', 
    'defect_analysis_agent',
    'costing_agent',
    'DefectAnalysisResult',
    'DefectAnalysisWorkflowResult',
    'DefectCostBreakdown',
    'DefectPricingFactors', 
    'LocationFactors'
]
