# FTA Origin Determination Tool

## Overview

This is a Flask-based web application designed to automate Free Trade Agreement (FTA) origin determination compliance for the EU-Vietnam trade agreement. The tool processes product costing sheets and performs a systematic 7-step workflow to determine whether products qualify for preferential treatment under FTA rules.

The application handles file uploads (Excel/CSV), extracts manufacturing cost data, analyzes materials and their origins, applies FTA rules specific to HS codes (particularly footwear and parts under headings 6401-6406), and generates compliance reports with detailed analysis steps and final determinations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework
- **Flask**: Core web framework with SQLAlchemy for database operations
- **Modular Design**: Separated concerns with distinct services for file processing, origin analysis, HS code validation, and FTA rules engine
- **Template-Based UI**: Jinja2 templates with Bootstrap for responsive interface

### Database Layer
- **SQLAlchemy ORM**: Database abstraction with two main models
  - `AnalysisSession`: Tracks analysis workflow, results, and metadata
  - `MaterialAnalysis`: Stores individual material cost and origin data
- **Flexible Database Support**: Configurable database URL (defaults to SQLite for development)

### File Processing Architecture
- **Multi-format Support**: Handles Excel (.xlsx, .xls) and CSV files using pandas and openpyxl
- **Column Mapping System**: Intelligent mapping of various column naming conventions to standardized internal schema
- **Data Validation**: Validates required fields and data formats before processing

### Business Logic Services
- **Origin Analyzer**: Implements 7-step FTA compliance workflow
- **FTA Rules Engine**: JSON-configurable rules system for different HS codes and trade agreements
- **HS Code Service**: Validation and description lookup for Harmonized System codes

### Analysis Workflow
- **Step-by-Step Process**: Systematic workflow from manufacturer verification to final cost percentage calculations
- **Rule-Based Decision Making**: Applies specific FTA rules based on HS code classifications
- **Threshold Compliance**: Calculates non-originating material percentages against FTA thresholds (typically 10% for footwear parts)

### Configuration Management
- **JSON-Based Rules**: Externalized FTA rules and HS code mappings in configuration files
- **Environment-Driven Settings**: Database URLs, file upload limits, and other settings via environment variables

## External Dependencies

### Core Dependencies
- **Flask Ecosystem**: Flask, Flask-SQLAlchemy for web framework and ORM
- **Data Processing**: pandas for data manipulation, openpyxl for Excel file handling
- **Database**: SQLAlchemy with support for SQLite (development) and PostgreSQL (production)

### Frontend Dependencies
- **Bootstrap**: Dark-themed UI framework via CDN
- **Feather Icons**: Icon library for consistent UI elements
- **Chart.js**: Data visualization for analysis results

### File Processing
- **File Upload Handling**: Werkzeug utilities for secure filename handling
- **Multiple Format Support**: pandas and openpyxl for comprehensive spreadsheet processing

### Configuration Files
- **FTA Rules**: JSON configuration in `config/fta_rules.json` defining trade agreement rules
- **HS Codes**: JSON lookup table in `config/hs_codes.json` for product classification descriptions

The application follows a service-oriented architecture pattern with clear separation between data processing, business logic, and presentation layers, making it maintainable and extensible for additional trade agreements or rule modifications.