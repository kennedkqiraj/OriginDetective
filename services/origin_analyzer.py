import logging
from models import AnalysisSession, MaterialAnalysis
from app import db
from services.hs_code_service import HSCodeService
from services.fta_rules_engine import FTARulesEngine
from services.gemini_explanation_service import GeminiExplanationService
from services.manufacturers import lookup as manu_lookup
import os

logger = logging.getLogger(__name__)

class OriginAnalyzer:
    def __init__(self):
        self.hs_service = HSCodeService()
        self.fta_engine = FTARulesEngine()
        self.gemini_service = GeminiExplanationService()
        self.analysis_steps = []
        self.missing_fields = []
    
    def analyze_origin(self, data, session_id):
        """Main origin analysis following the 7-step workflow"""
        session = AnalysisSession.query.get(session_id)
        
        try:
            # Step 1: Check manufacturer location
            manufacturer_result = self._step1_check_manufacturer(data, session)
            if not manufacturer_result['proceed']:
                self._finalize_analysis(session, 'non_originating', manufacturer_result['reason'])
                return session
            
            # Step 2: Find applicable HS Code
            hs_code_result = self._step2_find_hs_code(data, session)
            if not hs_code_result['proceed']:
                self._finalize_analysis(session, 'incomplete', hs_code_result['reason'])
                return session
            
            # Step 3: Look at FTA rules of origin
            fta_rules_result = self._step3_check_fta_rules(session)
            
            # Step 4: Identify non-VN and non-EU materials
            materials_result = self._step4_identify_materials(data, session)
            
            # Step 5: Check HS codes of problematic materials
            hs_check_result = self._step5_check_material_hs_codes(session)
            
            # Step 6: Check for Heading 6406
            heading_check_result = self._step6_check_heading_6406(session)
            if not heading_check_result['has_6406']:
                self._finalize_analysis(session, 'originating', 'No materials under heading 6406 found')
                return session
            
            # Step 7: Cost percentage analysis
            cost_result = self._step7_cost_analysis(session)
            
            # Final determination
            if cost_result['percentage'] <= 10:
                final_result = 'originating'
                reason = f"Materials under heading 6406 represent {cost_result['percentage']:.2f}% of total cost (≤10%)"
            else:
                final_result = 'non_originating'
                reason = f"Materials under heading 6406 represent {cost_result['percentage']:.2f}% of total cost (>10%)"
            
            self._finalize_analysis(session, final_result, reason)
            
        except Exception as e:
            logger.error(f"Error in origin analysis: {str(e)}")
            self._finalize_analysis(session, 'error', f"Analysis error: {str(e)}")
        
        return session
    
    def _step1_check_manufacturer(self, data, session):
        """
        Step 1: Check if manufacturer is Vietnamese using manufacturers.csv.
        Falls back to provided country fields if not found.
        """
        logger.info("Step 1: Checking manufacturer location")

        # Extract manufacturer fields from input data
        manufacturer = None
        manufacturer_id = None
        manufacturer_country = None

        for row in data:
            if not manufacturer and row.get("manufacturer"):
                manufacturer = str(row["manufacturer"]).strip()
            if not manufacturer_id and row.get("manufacturer_id"):
                manufacturer_id = str(row["manufacturer_id"]).strip()
            if not manufacturer_country and row.get("manufacturer_country"):
                manufacturer_country = str(row["manufacturer_country"]).strip()

        # Fallback to 'country_of_origin' if manufacturer_country not provided
        if not manufacturer_country:
            for row in data:
                if row.get("country_of_origin"):
                    manufacturer_country = str(row["country_of_origin"]).strip()
                    break

        if not manufacturer and not manufacturer_id:
            self.missing_fields.append("manufacturer")
            return {"proceed": False, "reason": "Manufacturer information missing"}

        # Update session with manufacturer string if available
        if manufacturer:
            session.manufacturer = manufacturer

        # 1) Primary check: manufacturers.csv lookup (by id, then name; case-insensitive)
        csv_result = manu_lookup(name=manufacturer, manufacturer_id=manufacturer_id)
        if csv_result.get("found"):
            is_vn = bool(csv_result.get("is_vietnam", False))
            session.manufacturer_is_vietnamese = is_vn
            self.analysis_steps.append({
                "step": 1,
                "description": f"Manufacturer matched in reference list: {csv_result['match']}",
                "is_vietnamese": is_vn,
                "proceed": is_vn
            })
            session.analysis_steps = self.analysis_steps
            db.session.commit()
            if not is_vn:
                return {"proceed": False, "reason": "Manufacturer found in reference list but not located in Vietnam."}
            return {"proceed": True, "reason": "Manufacturer found in Vietnam reference list."}

        # 2) Fallback: explicit country fields (case-insensitive)
        if manufacturer_country:
            country_norm = manufacturer_country.strip().lower()
            is_vn = (country_norm in {"vietnam", "viet nam"}) or (country_norm == "vn")
            session.manufacturer_is_vietnamese = is_vn
            self.analysis_steps.append({
                "step": 1,
                "description": f"No CSV match. Falling back to provided country '{manufacturer_country}'.",
                "is_vietnamese": is_vn,
                "proceed": is_vn
            })
            session.analysis_steps = self.analysis_steps
            db.session.commit()
            if not is_vn:
                return {"proceed": False, "reason": f"Provided manufacturer country is '{manufacturer_country}', not Vietnam."}
            return {"proceed": True, "reason": f"Manufacturer country provided as '{manufacturer_country}' (Vietnam)."}

        # 3) If nothing found
        self.missing_fields.append("manufacturer_country (or manufacturers.csv entry)")
        self.analysis_steps.append({
            "step": 1,
            "description": "Manufacturer not found in CSV and no country provided; unable to confirm Vietnam.",
            "is_vietnamese": False,
            "proceed": False
        })
        session.analysis_steps = self.analysis_steps
        db.session.commit()
        return {"proceed": False, "reason": "Manufacturer could not be verified (missing data)."}

    def _step2_find_hs_code(self, data, session):
        """Step 2: Find applicable HS Code of final product"""
        logger.info("Step 2: Finding final product HS code")
        
        # Look for final product HS code in the data
        final_hs_code = None
        
        # Check if there's a specific final product row or look for the most common HS code
        hs_codes = []
        for row in data:
            if 'hs_code' in row and row['hs_code']:
                hs_code = str(row['hs_code']).strip()
                if hs_code and hs_code.lower() not in ['nan', 'none', '']:
                    hs_codes.append(hs_code)
        
        if hs_codes:
            # Use the first HS code as final product (this logic could be improved)
            final_hs_code = hs_codes[0]
        
        if not final_hs_code:
            self.missing_fields.append('final_product_hs_code')
            return {'proceed': False, 'reason': 'Final product HS code not found'}
        
        # Validate HS code format
        if not self.hs_service.is_valid_hs_code(final_hs_code):
            return {'proceed': False, 'reason': f'Invalid HS code format: {final_hs_code}'}
        
        session.final_hs_code = final_hs_code
        
        step_result = {
            'step': 2,
            'description': 'Final product HS code identification',
            'final_hs_code': final_hs_code,
            'is_valid': True
        }
        
        self.analysis_steps.append(step_result)
        session.analysis_steps = self.analysis_steps
        db.session.commit()
        
        return {'proceed': True, 'hs_code': final_hs_code}
    
    def _step3_check_fta_rules(self, session):
        """Step 3: Look at FTA rules of origin"""
        logger.info("Step 3: Checking FTA rules of origin")
        
        if not session.final_hs_code:
            return {'proceed': False, 'reason': 'No HS code available for FTA rules check'}
        
        fta_rules = self.fta_engine.get_rules_for_hs_code(session.final_hs_code)
        
        step_result = {
            'step': 3,
            'description': 'FTA rules of origin check',
            'hs_code': session.final_hs_code,
            'applicable_rules': fta_rules
        }
        
        self.analysis_steps.append(step_result)
        session.analysis_steps = self.analysis_steps
        db.session.commit()
        
        return {'proceed': True, 'rules': fta_rules}
    
    def _step4_identify_materials(self, data, session):
        """Step 4: Identify non-VN and non-EU materials"""
        logger.info("Step 4: Identifying non-VN and non-EU materials")
        
        non_vn_eu_materials = []
        
        for row in data:
            if 'country_of_origin' not in row:
                continue
                
            country = str(row.get('country_of_origin', '')).strip().upper()
            
            if not country or country in ['NAN', 'NONE', '']:
                continue
            
            # Check if country is not VN or EU
            eu_countries = [
                'AT', 'BE', 'BG', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 
                'FR', 'GR', 'HR', 'HU', 'IE', 'IT', 'LT', 'LU', 'LV', 'MT', 
                'NL', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK'
            ]
            
            if country not in ['VN', 'VIETNAM'] and country not in eu_countries:
                # Create material analysis record
                material = MaterialAnalysis(
                    session_id=session.id,
                    material_name=str(row.get('material_name', 'Unknown')),
                    country_of_origin=country,
                    hs_code=str(row.get('hs_code', '')),
                    cost_per_pair=float(row.get('cost_per_pair', 0)) if row.get('cost_per_pair') else None,
                    is_problematic=True,
                    analysis_notes='Non-VN and non-EU material requiring further analysis'
                )
                db.session.add(material)
                non_vn_eu_materials.append(material)
        
        db.session.commit()
        
        step_result = {
            'step': 4,
            'description': 'Non-VN and non-EU materials identification',
            'materials_found': len(non_vn_eu_materials),
            'materials': [
                {
                    'name': m.material_name,
                    'country': m.country_of_origin,
                    'hs_code': m.hs_code
                } for m in non_vn_eu_materials
            ]
        }
        
        self.analysis_steps.append(step_result)
        session.analysis_steps = self.analysis_steps
        db.session.commit()
        
        return {'materials': non_vn_eu_materials}
    
    def _step5_check_material_hs_codes(self, session):
        """Step 5: Check HS codes of non-VN and non-EU materials"""
        logger.info("Step 5: Checking HS codes of problematic materials")
        
        materials = MaterialAnalysis.query.filter_by(session_id=session.id, is_problematic=True).all()
        
        for material in materials:
            if material.hs_code:
                # Validate and normalize HS code
                if self.hs_service.is_valid_hs_code(material.hs_code):
                    material.analysis_notes += f" | HS code {material.hs_code} validated"
                else:
                    material.analysis_notes += f" | Invalid HS code: {material.hs_code}"
                    self.missing_fields.append(f'valid_hs_code_for_{material.material_name}')
            else:
                material.analysis_notes += " | Missing HS code"
                self.missing_fields.append(f'hs_code_for_{material.material_name}')
        
        db.session.commit()
        
        step_result = {
            'step': 5,
            'description': 'HS codes validation for problematic materials',
            'materials_checked': len(materials)
        }
        
        self.analysis_steps.append(step_result)
        session.analysis_steps = self.analysis_steps
        db.session.commit()
        
        return {'checked': len(materials)}
    
    def _step6_check_heading_6406(self, session):
        """Step 6: Check if any materials fall under heading 6406"""
        logger.info("Step 6: Checking for heading 6406 materials")
        
        materials = MaterialAnalysis.query.filter_by(session_id=session.id, is_problematic=True).all()
        heading_6406_materials = []
        
        for material in materials:
            if material.hs_code and material.hs_code.startswith('6406'):
                heading_6406_materials.append(material)
                material.analysis_notes += " | Falls under heading 6406"
        
        db.session.commit()
        
        step_result = {
            'step': 6,
            'description': 'Heading 6406 check',
            'materials_in_6406': len(heading_6406_materials)
        }
        
        self.analysis_steps.append(step_result)
        session.analysis_steps = self.analysis_steps
        db.session.commit()
        
        return {
            'has_6406': len(heading_6406_materials) > 0,
            'materials': heading_6406_materials
        }
    
    def _step7_cost_analysis(self, session):
        """Step 7: Compare costs for materials under heading 6406"""
        logger.info("Step 7: Performing cost analysis")
        
        materials_6406 = MaterialAnalysis.query.filter(
            MaterialAnalysis.session_id == session.id,
            MaterialAnalysis.is_problematic == True,
            MaterialAnalysis.hs_code.like('6406%')
        ).all()
        
        # Get total FOB cost (this should come from the original data)
        # For now, we'll calculate based on available data
        all_materials = MaterialAnalysis.query.filter_by(session_id=session.id).all()
        total_cost = 0
        materials_6406_cost = 0
        missing_cost_data = []
        
        for material in all_materials:
            if material.cost_per_pair is not None:
                if material in materials_6406:
                    materials_6406_cost += material.cost_per_pair
                total_cost += material.cost_per_pair
            else:
                missing_cost_data.append(material.material_name)
        
        if missing_cost_data:
            for material_name in missing_cost_data:
                self.missing_fields.append(f'cost_per_pair_for_{material_name}')
        
        percentage = (materials_6406_cost / total_cost * 100) if total_cost > 0 else 0
        
        step_result = {
            'step': 7,
            'description': 'Cost percentage analysis',
            'materials_6406_cost': materials_6406_cost,
            'total_cost': total_cost,
            'percentage': percentage,
            'threshold_met': percentage <= 10,
            'missing_cost_data': missing_cost_data
        }
        
        self.analysis_steps.append(step_result)
        session.analysis_steps = self.analysis_steps
        db.session.commit()
        
        return step_result
    
    def _finalize_analysis(self, session, result, reason):
        """Finalize the analysis with result and reason"""
        session.final_result = result
        session.result_reason = reason
        session.missing_fields = self.missing_fields
        session.completed = True
        
        # Generate Gemini explanations
        try:
            # Prepare session data for Gemini
            session_data = {
                'manufacturer': session.manufacturer,
                'final_result': result,
                'result_reason': reason,
                'missing_fields': self.missing_fields,
                'analysis_steps': self.analysis_steps,
                'final_hs_code': session.final_hs_code
            }
            
            # Get materials data
            materials = MaterialAnalysis.query.filter_by(session_id=session.id).all()
            materials_data = [
                {
                    'material_name': m.material_name,
                    'country_of_origin': m.country_of_origin,
                    'hs_code': m.hs_code,
                    'cost_per_pair': m.cost_per_pair,
                    'is_problematic': m.is_problematic
                }
                for m in materials
            ]
            
            # Generate comprehensive explanation
            explanation = self.gemini_service.generate_origin_explanation(session_data, materials_data)
            if explanation:
                session.gemini_explanation = explanation
                logger.info(f"Generated Gemini explanation for session {session.id}")
            
            # Generate missing data analysis if there are missing fields
            if self.missing_fields:
                missing_analysis = self.gemini_service.generate_missing_data_analysis(
                    self.missing_fields, materials_data
                )
                if missing_analysis:
                    session.missing_data_analysis = missing_analysis
                    logger.info(f"Generated missing data analysis for session {session.id}")
                    
        except Exception as e:
            logger.error(f"Error generating Gemini explanations: {str(e)}")
        
        db.session.commit()
        logger.info(f"Analysis completed for session {session.id}: {result} - {reason}")
