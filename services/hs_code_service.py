import json
import os
import re
import logging

logger = logging.getLogger(__name__)

class HSCodeService:
    def __init__(self):
        self.hs_codes = self._load_hs_codes()
    
    def _load_hs_codes(self):
        """Load HS codes from configuration file"""
        try:
            config_path = os.path.join('config', 'hs_codes.json')
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("HS codes configuration file not found, using default structure")
            return {}
    
    def is_valid_hs_code(self, hs_code):
        """Validate HS code format"""
        if not hs_code:
            return False
        
        # Remove any spaces or dots
        hs_code = str(hs_code).replace(' ', '').replace('.', '')
        
        # HS codes should be 4, 6, 8, or 10 digits
        if not re.match(r'^\d{4,10}$', hs_code):
            return False
        
        return True
    
    def get_hs_code_description(self, hs_code):
        """Get description for HS code"""
        hs_code = str(hs_code).replace(' ', '').replace('.', '')
        
        # Try exact match first
        if hs_code in self.hs_codes:
            return self.hs_codes[hs_code]['description']
        
        # Try progressive matching (heading, then subheading)
        for length in [6, 4]:
            short_code = hs_code[:length]
            if short_code in self.hs_codes:
                return self.hs_codes[short_code]['description']
        
        return f"HS Code {hs_code} (Description not available)"
    
    def is_heading_6406(self, hs_code):
        """Check if HS code falls under heading 6406"""
        if not hs_code:
            return False
        
        hs_code = str(hs_code).replace(' ', '').replace('.', '')
        return hs_code.startswith('6406')
    
    def get_heading(self, hs_code):
        """Extract heading from HS code"""
        if not hs_code:
            return None
        
        hs_code = str(hs_code).replace(' ', '').replace('.', '')
        if len(hs_code) >= 4:
            return hs_code[:4]
        
        return None
