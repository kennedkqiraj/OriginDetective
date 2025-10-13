import json
import logging
import os
from typing import Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None

logger = logging.getLogger(__name__)

class GeminiExplanationService:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client if API key is available"""
        if not GEMINI_AVAILABLE:
            logger.warning("Google Gemini SDK not available")
            return
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            return
        
        try:
            if genai is not None:
                self.client = genai.Client(api_key=api_key)
                logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Gemini service is available"""
        return self.client is not None
    
    def generate_origin_explanation(self, session_data: Dict[str, Any], materials_data: list) -> Optional[str]:
        """
        Generate comprehensive explanation of origin determination result
        
        Args:
            session_data: Dictionary containing analysis session information
            materials_data: List of material analysis data
            
        Returns:
            Generated explanation text or None if service unavailable
        """
        if not self.is_available():
            return self._generate_fallback_explanation(session_data, materials_data)
        
        try:
            prompt = self._build_explanation_prompt(session_data, materials_data)
            
            config = None
            if types is not None:
                config = types.GenerateContentConfig(
                    max_output_tokens=800,
                    temperature=0.3
                )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config
            )
            
            if response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini")
                return self._generate_fallback_explanation(session_data, materials_data)
                
        except Exception as e:
            logger.error(f"Error generating Gemini explanation: {str(e)}")
            return self._generate_fallback_explanation(session_data, materials_data)
    
    def _build_explanation_prompt(self, session_data: Dict[str, Any], materials_data: list) -> str:
        """Build the prompt for Gemini to generate explanation"""
        
        # Prepare analysis data
        manufacturer = session_data.get('manufacturer', 'Unknown')
        final_result = session_data.get('final_result', 'incomplete')
        result_reason = session_data.get('result_reason', 'No reason provided')
        missing_fields = session_data.get('missing_fields', [])
        analysis_steps = session_data.get('analysis_steps', [])
        final_hs_code = session_data.get('final_hs_code', 'Not determined')
        
        # Count materials by type
        total_materials = len(materials_data)
        problematic_materials = [m for m in materials_data if m.get('is_problematic', False)]
        materials_6406 = [m for m in materials_data if m.get('hs_code', '').startswith('6406')]
        
        prompt = f"""
You are an expert in Free Trade Agreement (FTA) compliance and origin determination rules, specifically for the EU-Vietnam FTA. 

Analyze the following FTA origin determination case and provide a comprehensive, professional explanation suitable for business stakeholders.

**CASE DETAILS:**
- Manufacturer: {manufacturer}
- Final Product HS Code: {final_hs_code}
- Final Determination: {final_result.upper()}
- System Reason: {result_reason}
- Total Materials Analyzed: {total_materials}
- Problematic Materials (non-VN/non-EU): {len(problematic_materials)}
- Materials under Heading 6406: {len(materials_6406)}

**ANALYSIS STEPS COMPLETED:**
{self._format_analysis_steps(analysis_steps)}

**MISSING DATA FIELDS:**
{', '.join(missing_fields) if missing_fields else 'None'}

**MATERIAL DETAILS:**
{self._format_materials_summary(materials_data)}

Please provide a clear, professional explanation that covers:

1. **Executive Summary**: Brief conclusion with the determination result
2. **Key Factors**: Main reasons influencing the determination
3. **Compliance Analysis**: How EU-Vietnam FTA rules were applied
4. **Data Quality**: Impact of any missing information
5. **Recommendations**: Next steps or actions needed (if any)

Write in a professional tone suitable for trade compliance officers and business managers. Be specific about FTA rules and thresholds where relevant. Keep the explanation concise but comprehensive (4-6 paragraphs).
"""
        return prompt
    
    def _format_analysis_steps(self, steps: list) -> str:
        """Format analysis steps for the prompt"""
        if not steps:
            return "No detailed steps available"
        
        formatted_steps = []
        for step in steps:
            step_num = step.get('step', '?')
            description = step.get('description', 'Unknown step')
            formatted_steps.append(f"Step {step_num}: {description}")
        
        return '\n'.join(formatted_steps)
    
    def _format_materials_summary(self, materials_data: list) -> str:
        """Format materials summary for the prompt"""
        if not materials_data:
            return "No material data available"
        
        summary_lines = []
        for material in materials_data[:10]:  # Limit to first 10 materials
            name = material.get('material_name', 'Unknown')
            country = material.get('country_of_origin', 'Unknown')
            hs_code = material.get('hs_code', 'N/A')
            cost = material.get('cost_per_pair', 'N/A')
            problematic = "⚠️" if material.get('is_problematic', False) else "✓"
            
            summary_lines.append(f"- {name} | {country} | HS: {hs_code} | Cost: {cost} {problematic}")
        
        if len(materials_data) > 10:
            summary_lines.append(f"... and {len(materials_data) - 10} more materials")
        
        return '\n'.join(summary_lines)
    
    def _generate_fallback_explanation(self, session_data: Dict[str, Any], materials_data: list) -> str:
        """Generate basic explanation when Gemini is not available"""
        
        final_result = session_data.get('final_result', 'incomplete')
        result_reason = session_data.get('result_reason', 'Analysis could not be completed')
        missing_fields = session_data.get('missing_fields', [])
        manufacturer = session_data.get('manufacturer', 'Not identified')
        
        explanation = f"""**FTA Origin Determination Analysis**

**Final Result:** {final_result.upper().replace('_', ' ')}

**Summary:** Based on the EU-Vietnam FTA compliance analysis, this product has been determined as {final_result.replace('_', ' ')}. {result_reason}

**Manufacturer Analysis:** The manufacturer identified was "{manufacturer}". For products to qualify for preferential treatment under the EU-Vietnam FTA, they must be manufactured in Vietnam by a Vietnamese entity.

**Analysis Process:** The system followed the standard 7-step compliance workflow, examining manufacturer location, HS codes, FTA rules, material origins, and cost thresholds as applicable.
"""

        if missing_fields:
            explanation += f"""
**Data Quality Issues:** The analysis identified missing or incomplete data fields: {', '.join(missing_fields)}. Complete and accurate data is essential for reliable origin determination.
"""

        explanation += """
**Next Steps:** For a complete assessment, ensure all required data fields are populated in your costing sheet. Consider consulting with trade compliance specialists for complex cases or when dealing with substantial manufacturing operations.

*Note: This automated analysis provides preliminary guidance. Final origin determinations should be validated by qualified trade compliance professionals.*
"""

        return explanation
    
    def generate_missing_data_analysis(self, missing_fields: list, materials_data: list) -> Optional[str]:
        """
        Generate analysis of missing data and its impact on origin determination
        
        Args:
            missing_fields: List of missing data fields
            materials_data: List of material data
            
        Returns:
            Analysis text or None if service unavailable
        """
        if not self.is_available() or not missing_fields:
            return None
        
        try:
            prompt = f"""
As an FTA compliance expert, analyze the impact of missing data on origin determination accuracy.

**Missing Data Fields:**
{', '.join(missing_fields)}

**Available Materials Data:** {len(materials_data)} materials with varying completeness

Provide a brief analysis (2-3 paragraphs) covering:
1. Which missing fields are most critical for accurate origin determination
2. How these gaps affect compliance confidence
3. Recommended data collection priorities

Keep the tone professional and actionable for business users.
"""
            
            config = None
            if types is not None:
                config = types.GenerateContentConfig(
                    max_output_tokens=400,
                    temperature=0.3
                )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config
            )
            
            return response.text.strip() if response.text else None
            
        except Exception as e:
            logger.error(f"Error generating missing data analysis: {str(e)}")
            return None