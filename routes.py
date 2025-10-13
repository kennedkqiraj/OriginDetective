import os
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from app import app, db
from models import AnalysisSession, MaterialAnalysis
from services.file_processor import FileProcessor
from services.origin_analyzer import OriginAnalyzer
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Create new analysis session
            session = AnalysisSession(filename=filename)
            db.session.add(session)
            db.session.commit()
            
            try:
                # Process the file
                processor = FileProcessor()
                data = processor.process_file(filepath)
                
                if not data:
                    flash('Could not process the uploaded file. Please check the format.', 'error')
                    return redirect(url_for('upload_file'))
                
                # Start origin analysis
                analyzer = OriginAnalyzer()
                result = analyzer.analyze_origin(data, session.id)
                
                return redirect(url_for('view_analysis', session_id=session.id))
                
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(url_for('upload_file'))
        else:
            flash('Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.', 'error')
    
    return render_template('upload.html')

@app.route('/analysis/<int:session_id>')
def view_analysis(session_id):
    session = AnalysisSession.query.get_or_404(session_id)
    materials = MaterialAnalysis.query.filter_by(session_id=session_id).all()
    
    return render_template('analysis.html', session=session, materials=materials)

@app.route('/results/<int:session_id>')
def view_results(session_id):
    session = AnalysisSession.query.get_or_404(session_id)
    materials = MaterialAnalysis.query.filter_by(session_id=session_id).all()
    
    return render_template('results.html', session=session, materials=materials)

@app.route('/api/analysis/<int:session_id>/status')
def get_analysis_status(session_id):
    session = AnalysisSession.query.get_or_404(session_id)
    return jsonify({
        'completed': session.completed,
        'steps': session.analysis_steps,
        'result': session.final_result,
        'reason': session.result_reason,
        'missing_fields': session.missing_fields
    })

@app.route('/download/<int:session_id>')
def download_results(session_id):
    session = AnalysisSession.query.get_or_404(session_id)
    
    # Generate results file
    from services.file_processor import FileProcessor
    processor = FileProcessor()
    results_file = processor.generate_results_report(session_id)
    
    return send_file(results_file, as_attachment=True, 
                    download_name=f'fta_origin_results_{session_id}.xlsx')

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum file size is 16MB.', 'error')
    return redirect(url_for('upload_file'))
