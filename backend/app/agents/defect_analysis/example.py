#!/usr/bin/env python3
"""
Example usage of the defect analysis workflow
"""

import asyncio
from pathlib import Path
import sys

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

async def main():
    """Example of running the defect analysis workflow"""
    print("🏗️ Building Defect Analysis Workflow")
    print("=" * 50)
    
    # Import after adding to path
    from app.agents.defect_analysis.workflow import analyze_building_defect
    
    # Define paths to test images
    data_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'defect_photo_pairs'
    photo1 = data_dir / '1e1ac56a-6cf8-4c04-9f53-27ae6f8d9151 copy.jpg'
    photo2 = data_dir / '246d69c9-64e3-4bd1-b9cb-03d0a9f0bfdd copy.jpg'
    
    # Building address for context
    building_address = "123 Main Street, Geelong, Victoria 3220, Australia"
    
    try:
        print(f"📸 Processing defect photos:")
        print(f"  Close-up: {photo1.name}")
        print(f"  Context: {photo2.name}")
        print(f"🏠 Building: {building_address}")
        
        # Check files exist
        if not photo1.exists():
            print(f"❌ Photo 1 not found: {photo1}")
            return
        if not photo2.exists():
            print(f"❌ Photo 2 not found: {photo2}")
            return
        
        print(f"\n🤖 Starting AI analysis workflow...")
        
        # Run the analysis
        result = await analyze_building_defect(photo1, photo2, building_address)
        
        print(f"\n✅ Analysis Complete!")
        print("=" * 50)
        
        # Display results
        if hasattr(result, 'analyzed_defects') and result.analyzed_defects:
            defect = result.analyzed_defects[0]
            
            print(f"📍 Location: {result.building_address}")
            print(f"🔍 Defect Category: {defect.defect_category}")
            print(f"🏷️  Defect Type: {defect.defect_type}")
            print(f"📝 Description: {defect.description}")
            print(f"🔧 Rectification: {defect.rectification_works}")
            print(f"⚠️  Priority: {defect.priority}")
            print(f"💰 Cost Estimate: ${defect.cost_estimate:.2f}")
            print(f"📊 Confidence: {defect.cost_confidence:.1%}")
            
            print(f"\n💵 Cost Breakdown:")
            print(f"  Materials: ${defect.cost_breakdown.materials:.2f}")
            print(f"  Labour: ${defect.cost_breakdown.labor:.2f}")
            print(f"  Equipment: ${defect.cost_breakdown.equipment:.2f}")
            
            print(f"\n📈 Pricing Factors:")
            print(f"  Complexity: {defect.pricing_factors.complexity}")
            print(f"  Access: {defect.pricing_factors.access_difficulty}")
            print(f"  Region: {defect.location_factors.region}")
            
        else:
            print(f"Result: {result}")
            
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        print("\nMake sure test images exist at:")
        print(f"  {photo1}")
        print(f"  {photo2}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
