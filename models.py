from app import db
from datetime import datetime
from sqlalchemy import JSON

class AnalysisSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    manufacturer = db.Column(db.String(255))
    final_hs_code = db.Column(db.String(20))
    analysis_steps = db.Column(JSON)
    final_result = db.Column(db.String(20))  # 'originating' or 'non_originating'
    result_reason = db.Column(db.Text)
    missing_fields = db.Column(JSON)
    completed = db.Column(db.Boolean, default=False)
    gemini_explanation = db.Column(db.Text)  # AI-generated explanation
    missing_data_analysis = db.Column(db.Text)  # AI analysis of missing data
    
    def __repr__(self):
        return f'<AnalysisSession {self.filename}>'

class MaterialAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('analysis_session.id'), nullable=False)
    material_name = db.Column(db.String(255))
    country_of_origin = db.Column(db.String(10))
    hs_code = db.Column(db.String(20))
    cost_per_pair = db.Column(db.Float)
    is_problematic = db.Column(db.Boolean, default=False)
    analysis_notes = db.Column(db.Text)
    
    session = db.relationship('AnalysisSession', backref=db.backref('materials', lazy=True))
    
    def __repr__(self):
        return f'<MaterialAnalysis {self.material_name}>'
