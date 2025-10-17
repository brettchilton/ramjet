from app.agents.defect_analysis.agent_definitions import defect_analysis_agent
from pathlib import Path
import base64
from agents import Runner, enable_verbose_stdout_logging

# Enable verbose logging
enable_verbose_stdout_logging()

class DefectAnalysisWorkflow:
    """
    Main workflow for analyzing building defects using AI agents.
    
    This workflow:
    1. Takes defect photos and building address
    2. Runs DefectAnalysisAgent to analyze the defect
    3. Hands off to CostingAgent for pricing
    4. Returns structured results with analysis and cost estimates
    """
    
    def __init__(self):
        self.analysis_agent = defect_analysis_agent
    
    @staticmethod
    def encode_image(image_path: Path) -> str:
        """Encode image to base64 for OpenAI API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def prepare_defect_input(self, photo1_path: Path, photo2_path: Path, building_address: str):
        """
        Prepare input for defect analysis with two photos and building address
        
        Args:
            photo1_path: Path to close-up defect photo
            photo2_path: Path to context defect photo  
            building_address: Full building address for pricing context
        """
        # Encode images
        image1_base64 = self.encode_image(photo1_path)
        image2_base64 = self.encode_image(photo2_path)
        
        # Create the input with images in the proper format for OpenAI SDK
        input_with_images = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Please analyze these two building defect photos of the same defect from different perspectives. The building is located at: {building_address}"
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image1_base64}",
                        "detail": "high"
                    },
                    {
                        "type": "input_image", 
                        "image_url": f"data:image/jpeg;base64,{image2_base64}",
                        "detail": "high"
                    }
                ]
            }
        ]
        
        return input_with_images
    
    async def analyze_defect(self, photo1_path: Path, photo2_path: Path, building_address: str):
        """
        Run the complete defect analysis workflow
        
        Args:
            photo1_path: Path to close-up defect photo
            photo2_path: Path to context defect photo
            building_address: Full building address for pricing context
            
        Returns:
            DefectAnalysisWorkflowResult with complete analysis and costing
        """
        # Prepare input
        workflow_input = self.prepare_defect_input(photo1_path, photo2_path, building_address)
        
        # Run the workflow starting with DefectAnalysisAgent
        result = await Runner.run(self.analysis_agent, workflow_input)
        
        return result.final_output

# Convenience function for direct usage
async def analyze_building_defect(photo1_path: Path, photo2_path: Path, building_address: str):
    """
    Convenience function to run defect analysis workflow
    
    Args:
        photo1_path: Path to close-up defect photo
        photo2_path: Path to context defect photo
        building_address: Full building address for pricing context
        
    Returns:
        DefectAnalysisWorkflowResult with complete analysis and costing
    """
    workflow = DefectAnalysisWorkflow()
    return await workflow.analyze_defect(photo1_path, photo2_path, building_address)
