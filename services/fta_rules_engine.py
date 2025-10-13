import json
import os
import logging

logger = logging.getLogger(__name__)

class FTARulesEngine:
    def __init__(self):
        self.fta_rules = self._load_fta_rules()
    
    def _load_fta_rules(self):
        """Load FTA rules from configuration file"""
        # Try agreement.json first, then fallback to fta_rules.json
        for filename in ['agreement.json', 'fta_rules.json']:
            try:
                config_path = os.path.join('config', filename)
                with open(config_path, 'r') as f:
                    logger.info(f"Loaded FTA rules from {filename}")
                    return json.load(f)
            except FileNotFoundError:
                continue
        
        logger.warning("No FTA rules configuration file found, using default rules")
        return self._get_default_rules()
    
    def _get_default_rules(self):
        """Default FTA rules for common scenarios"""
        return {
            "default": {
                "description": "General rules for origin determination",
                "rules": [
                    "Manufacturing or processing must result in a change in tariff classification",
                    "Value-added content must meet minimum thresholds",
                    "Specific manufacturing processes may be required"
                ]
            },
            "6406": {
                "description": "Parts of footwear; removable in-soles, heel cushions",
                "rules": [
                    "Non-originating materials must not exceed 10% of FOB value",
                    "Manufacturing must involve substantial transformation",
                    "Assembly and finishing operations must occur in the originating country"
                ],
                "threshold": 10
            }
        }
    
    def get_rules_for_hs_code(self, hs_code):
        """Get applicable FTA rules for specific HS code"""
        if not hs_code:
            return self.fta_rules.get('default', {})
        
        hs_code = str(hs_code).replace(' ', '').replace('.', '')
        
        # Try exact match first
        if hs_code in self.fta_rules:
            return self.fta_rules[hs_code]
        
        # Try heading match
        heading = hs_code[:4] if len(hs_code) >= 4 else hs_code
        if heading in self.fta_rules:
            return self.fta_rules[heading]
        
        # Return default rules
        return self.fta_rules.get('default', {})
    
    def get_threshold_for_hs_code(self, hs_code):
        """Get cost threshold percentage for specific HS code"""
        rules = self.get_rules_for_hs_code(hs_code)
        return rules.get('threshold', 10)  # Default 10% threshold
    
    def check_origin_compliance(self, hs_code, non_originating_percentage):
        """Check if origin determination complies with FTA rules"""
        threshold = self.get_threshold_for_hs_code(hs_code)
        
        return {
            'compliant': non_originating_percentage <= threshold,
            'threshold': threshold,
            'percentage': non_originating_percentage,
            'rules': self.get_rules_for_hs_code(hs_code)
        }
