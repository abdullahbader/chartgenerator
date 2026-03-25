from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
import os
import base64
from io import BytesIO
import kaleido
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import tempfile

app = Flask(__name__)
# Allow uploads up to 50MB (CSV/Excel files can be large)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
# Configure CORS to allow all origins and methods
CORS(app, 
     resources={r"/api/*": {
         "origins": "*",
         "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
         "allow_headers": ["Content-Type", "Authorization"]
     }}, 
     supports_credentials=True)

# Add CORS headers to all responses (needed for file upload)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Add logging for debugging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
DATASETS_FOLDER = os.path.join(os.path.dirname(__file__), 'sample_datasets')
FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATASETS_FOLDER, exist_ok=True)

# Store uploaded datasets in memory (in production, use a database)
datasets = {}

# Built-in dummy dataset for testing without upload
DUMMY_DATASET_ID = 'dummy_sample'
_dummy_df = pd.DataFrame({
    'Category': ['Red', 'Blue', 'Green', 'Red', 'Blue', 'Green', 'Red', 'Blue'],
    'Value': [10, 25, 15, 20, 30, 18, 12, 22]
})

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum upload size is 50MB.'}), 413

@app.route('/')
def index():
    """Serve the frontend app"""
    index_path = os.path.join(FRONTEND_FOLDER, 'index.html')
    if os.path.exists(index_path):
        response = send_file(index_path)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    return jsonify({'error': 'Frontend not found'}), 404

# Variable definition: key (used in API), label, required (bool), description (optional)
_VAR_ONE = [{'key': 'column', 'label': 'Column', 'required': True, 'description': 'Category or value column to visualize.'}]
_VAR_SCATTER = [
    {'key': 'x_column', 'label': 'X axis', 'required': True, 'description': 'Variable for the horizontal axis.'},
    {'key': 'y_column', 'label': 'Y axis', 'required': True, 'description': 'Variable for the vertical axis.'},
    {'key': 'size_column', 'label': 'Bubble size', 'required': False, 'description': 'Optional. Size of points; useful for emphasis.'},
]
_VAR_BUBBLE = [
    {'key': 'x_column', 'label': 'X axis', 'required': True, 'description': 'Variable for the horizontal axis.'},
    {'key': 'y_column', 'label': 'Y axis', 'required': True, 'description': 'Variable for the vertical axis.'},
    {'key': 'size_column', 'label': 'Size', 'required': False, 'description': 'Optional. Third dimension as bubble size; if omitted, a default size is used.'},
]

# Up to 100 chart types with per-chart variable requirements (required vs optional)
CHART_TYPES = [
    {'id': 'pie', 'name': 'Pie Chart', 'description': 'Display proportions of a whole', 'variables': _VAR_ONE, 'category': 'Part-of-whole'},
    {'id': 'donut', 'name': 'Donut Chart', 'description': 'Pie chart with a hollow center', 'variables': _VAR_ONE, 'category': 'Part-of-whole'},
    {'id': 'treemap', 'name': 'Treemap', 'description': 'Hierarchical data as nested rectangles', 'variables': _VAR_ONE, 'category': 'Part-of-whole'},
    {'id': 'sunburst', 'name': 'Sunburst', 'description': 'Hierarchical data as concentric rings', 'variables': _VAR_ONE, 'category': 'Part-of-whole'},
    {'id': 'funnel', 'name': 'Funnel Chart', 'description': 'Stages in a process', 'variables': _VAR_ONE, 'category': 'Part-of-whole'},
    {'id': 'polar_area', 'name': 'Polar Area', 'description': 'Values as sectors in a circle', 'variables': _VAR_ONE, 'category': 'Part-of-whole'},
    {'id': 'bar', 'name': 'Bar Chart', 'description': 'Compare values across categories', 'variables': _VAR_ONE, 'category': 'Comparison'},
    {'id': 'horizontal_bar', 'name': 'Horizontal Bar', 'description': 'Bar chart with horizontal bars', 'variables': _VAR_ONE, 'category': 'Comparison'},
    {'id': 'grouped_bar', 'name': 'Grouped Bar', 'description': 'Bars grouped side by side', 'variables': _VAR_ONE, 'category': 'Comparison'},
    {'id': 'stacked_bar', 'name': 'Stacked Bar', 'description': 'Bars stacked by category', 'variables': _VAR_ONE, 'category': 'Comparison'},
    {'id': 'radar', 'name': 'Radar Chart', 'description': 'Multivariate data on axes', 'variables': _VAR_ONE, 'category': 'Comparison'},
    {'id': 'line', 'name': 'Line Chart', 'description': 'Trends over time or continuous data', 'variables': _VAR_ONE, 'category': 'Trend'},
    {'id': 'line_marker', 'name': 'Line with Markers', 'description': 'Line chart with data point markers', 'variables': _VAR_ONE, 'category': 'Trend'},
    {'id': 'area', 'name': 'Area Chart', 'description': 'Cumulative change over time', 'variables': _VAR_ONE, 'category': 'Trend'},
    {'id': 'area_stacked', 'name': 'Stacked Area', 'description': 'Stacked area over time', 'variables': _VAR_ONE, 'category': 'Trend'},
    {'id': 'histogram', 'name': 'Histogram', 'description': 'Distribution of a single variable', 'variables': _VAR_ONE, 'category': 'Distribution'},
    {'id': 'box', 'name': 'Box Plot', 'description': 'Distribution and quartiles', 'variables': _VAR_ONE, 'category': 'Distribution'},
    {'id': 'scatter', 'name': 'Scatter Plot', 'description': 'Relationship between two variables', 'variables': _VAR_SCATTER, 'category': 'Distribution'},
    {'id': 'bubble', 'name': 'Bubble Chart', 'description': 'Scatter with size as third dimension', 'variables': _VAR_BUBBLE, 'category': 'Distribution'},
    {'id': 'heatmap', 'name': 'Heatmap', 'description': 'Values as colors in a matrix', 'variables': _VAR_ONE, 'category': 'Other'},
]


@app.route('/api/chart-types', methods=['GET'])
def get_chart_types():
    """Get available chart types (up to 100)"""
    return jsonify({'chart_types': CHART_TYPES})

@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    """Get list of available datasets"""
    # Always include dummy dataset first for testing without upload
    result = [
        {'id': DUMMY_DATASET_ID, 'name': 'Dummy (test data)', 'type': 'sample'}
    ]
    # Load sample datasets from folder
    if os.path.exists(DATASETS_FOLDER):
        for file in os.listdir(DATASETS_FOLDER):
            if file.endswith(('.csv', '.xlsx', '.xls')):
                result.append({
                    'id': f'sample_{file}',
                    'name': file,
                    'type': 'sample'
                })
    # Add uploaded datasets
    for k, v in datasets.items():
        result.append({'id': k, 'name': v['name'], 'type': 'uploaded'})
    
    return jsonify({'datasets': result})

def _upload_response(data, status, request):
    """Return JSON or HTML (for form submit in iframe) response"""
    if request.form.get('return_html') == '1':
        html_body = f'''<!DOCTYPE html><html><body><script>
window.parent.postMessage({{type:'upload_result',data:{json.dumps(data)},status:{status}}}, '*');
</script></body></html>'''
        from flask import Response
        return Response(html_body, status=200, mimetype='text/html')
    return (jsonify(data), status) if status >= 400 else jsonify(data)

@app.route('/api/datasets/upload', methods=['POST', 'OPTIONS'])
def upload_dataset():
    """Upload a new dataset"""
    if request.method == 'OPTIONS':
        resp = jsonify({'status': 'ok'})
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        resp.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return resp
    
    logger.info(f"Upload request received. Method: {request.method}")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Files in request: {list(request.files.keys())}")
    logger.info(f"Form data keys: {list(request.form.keys())}")
    
    if 'file' not in request.files:
        logger.error("No 'file' key in request.files")
        return _upload_response({'error': 'No file provided. Form field must be named "file"'}, 400, request)
    
    file = request.files['file']
    if not file:
        logger.error("File object is None")
        return _upload_response({'error': 'File object is None'}, 400, request)
    
    logger.info(f"File received: {file.filename}, Content-Type: {file.content_type}, Size: {file.content_length if hasattr(file, 'content_length') else 'unknown'}")
    
    if file.filename == '':
        logger.error("Empty filename")
        return _upload_response({'error': 'No file selected'}, 400, request)
    
    return_html = request.form.get('return_html') == '1'
    filepath = None  # Set before try so except block can safely check/remove

    try:
        # Read dataset - need to save file first, then read
        dataset_id = f"upload_{len(datasets)}"
        safe_filename = file.filename.replace(' ', '_').replace('(', '').replace(')', '')
        filepath = os.path.join(UPLOAD_FOLDER, f"{dataset_id}_{safe_filename}")
        
        # Save file to disk first
        file.save(filepath)
        
        # Now read the saved file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            if os.path.exists(filepath):
                os.remove(filepath)
            return _upload_response({'error': 'Unsupported format. Use CSV or Excel.'}, 400, request)
        
        # Store dataset
        datasets[dataset_id] = {
            'name': file.filename,
            'data': df.to_dict('records'),
            'columns': df.columns.tolist(),
            'filepath': filepath  # Store file path for R code generation
        }
        
        logger.info(f"Dataset uploaded successfully: {dataset_id}, Rows: {len(df)}, Columns: {len(df.columns)}")
        
        return _upload_response({
            'id': dataset_id,
            'name': file.filename,
            'columns': df.columns.tolist(),
            'row_count': len(df)
        }, 200, request)
    except pd.errors.EmptyDataError:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return _upload_response({'error': 'The uploaded file is empty or could not be read.'}, 400, request)
    except pd.errors.ParserError as e:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return _upload_response({'error': f'Error parsing file: {str(e)}'}, 400, request)
    except Exception as e:
        import traceback
        error_msg = str(e)
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
        return _upload_response({'error': f'Error uploading dataset: {error_msg}'}, 500, request)

@app.route('/api/datasets/<dataset_id>/columns', methods=['GET'])
def get_dataset_columns(dataset_id):
    """Get columns for a specific dataset"""
    try:
        if dataset_id == DUMMY_DATASET_ID:
            return jsonify({
                'columns': _dummy_df.columns.tolist(),
                'data_types': _dummy_df.dtypes.astype(str).to_dict()
            })
        if dataset_id.startswith('sample_'):
            # Load sample dataset
            filename = dataset_id.replace('sample_', '')
            filepath = os.path.join(DATASETS_FOLDER, filename)
            
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(filepath)
            else:
                return jsonify({'error': 'Unsupported file format'}), 400
            
            return jsonify({
                'columns': df.columns.tolist(),
                'data_types': df.dtypes.astype(str).to_dict()
            })
        else:
            # Get uploaded dataset
            if dataset_id not in datasets:
                return jsonify({'error': 'Dataset not found'}), 404
            
            dataset = datasets[dataset_id]
            return jsonify({
                'columns': dataset['columns'],
                'data_types': {col: 'object' for col in dataset['columns']}
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/preview', methods=['GET'])
def get_dataset_preview(dataset_id):
    """Get first N rows of a dataset for preview (columns + rows)."""
    try:
        df = load_dataset(dataset_id)
        n = min(int(request.args.get('rows', 10)), 50)
        rows = df.head(n).fillna('').to_dict('records')
        # Convert non-serializable types to string
        for r in rows:
            for k, v in list(r.items()):
                if not isinstance(v, (str, int, float, bool, type(None))):
                    r[k] = str(v)
        return jsonify({
            'columns': df.columns.tolist(),
            'rows': rows,
            'row_count': len(df)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/columns/<column>/values', methods=['GET'])
def get_column_values(dataset_id, column):
    """Get unique values for a specific column"""
    try:
        df = load_dataset(dataset_id)
        
        if column not in df.columns:
            return jsonify({'error': 'Column not found'}), 404
        
        unique_values = df[column].unique().tolist()
        # Convert to strings and sort
        unique_values = sorted([str(v) for v in unique_values])
        
        return jsonify({
            'column': column,
            'values': unique_values,
            'count': len(unique_values)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _normalize_columns(chart_type, data):
    """Build columns dict from request: accept 'column' (legacy) or 'columns' (per-variable)."""
    columns = data.get('columns')
    if columns is not None and isinstance(columns, dict):
        return columns
    # Legacy: single 'column' key
    col = data.get('column')
    if col:
        return {'column': col}
    return {}


def _get_chart_type_info(chart_type):
    """Return chart type dict with variables, or None."""
    for ct in CHART_TYPES:
        if ct.get('id') == chart_type:
            return ct
    return None


def _validate_columns(chart_type, columns):
    """Raise ValueError if required variables are missing."""
    info = _get_chart_type_info(chart_type)
    if not info or not info.get('variables'):
        return
    for var in info['variables']:
        if var.get('required') and not columns.get(var['key']):
            raise ValueError(f"Missing required variable: {var['label']} ({var['key']})")


@app.route('/api/charts/generate', methods=['POST'])
def generate_chart():
    """Generate a chart based on user specifications"""
    data = request.json or {}
    
    chart_type = data.get('chart_type')
    dataset_id = data.get('dataset_id')
    columns = _normalize_columns(chart_type, data)
    customization = data.get('customization', {})
    
    try:
        _validate_columns(chart_type, columns)
        df = load_dataset(dataset_id)
        
        if chart_type in CHART_GENERATORS:
            chart_data = CHART_GENERATORS[chart_type](df, columns, customization)
        else:
            return jsonify({
                'error': f'Chart type "{chart_type}" is not yet implemented. Try Pie, Bar, Line, or another from the list.'
            }), 400
        
        return jsonify(chart_data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/charts/export', methods=['POST'])
def export_chart():
    """Export chart in various formats"""
    data = request.json or {}
    
    chart_type = data.get('chart_type')
    dataset_id = data.get('dataset_id')
    columns = _normalize_columns(chart_type, data)
    customization = data.get('customization', {})
    export_format = data.get('format')  # 'png', 'pdf', 'html', 'r'
    
    try:
        _validate_columns(chart_type, columns)
        df = load_dataset(dataset_id)
        
        if export_format == 'r':
            r_code = generate_r_code(chart_type, df, columns, customization, dataset_id)
            return jsonify({'format': 'r', 'code': r_code})
        elif export_format == 'python':
            py_code = generate_python_code(chart_type, df, columns, customization, dataset_id)
            return jsonify({'format': 'python', 'code': py_code})
        elif export_format == 'svg':
            svg_data = generate_svg(chart_type, df, columns, customization)
            return jsonify({'format': 'svg', 'content': svg_data})
        elif export_format == 'png':
            img_data = generate_png(chart_type, df, columns, customization)
            return jsonify({'format': 'png', 'data': img_data})
        elif export_format == 'pdf':
            pdf_data = generate_pdf(chart_type, df, columns, customization)
            return jsonify({'format': 'pdf', 'data': pdf_data})
        elif export_format == 'html':
            html_content = generate_html(chart_type, df, columns, customization)
            return jsonify({'format': 'html', 'content': html_content})
        else:
            return jsonify({'error': 'Unsupported export format'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        return jsonify({'error': f'Export error: {str(e)}', 'traceback': traceback.format_exc()}), 500

def load_dataset(dataset_id):
    """Load dataset by ID"""
    if dataset_id == DUMMY_DATASET_ID:
        return _dummy_df.copy()
    if dataset_id.startswith('sample_'):
        filename = dataset_id.replace('sample_', '')
        filepath = os.path.join(DATASETS_FOLDER, filename)
        
        if not os.path.exists(filepath):
            raise ValueError(f'Sample dataset file not found: {filename}')
        
        if filename.endswith('.csv'):
            return pd.read_csv(filepath)
        elif filename.endswith(('.xlsx', '.xls')):
            return pd.read_excel(filepath)
        else:
            raise ValueError(f'Unsupported file format for sample dataset: {filename}')
    else:
        # For uploaded datasets, try to load from memory first
        if dataset_id in datasets:
            return pd.DataFrame(datasets[dataset_id]['data'])
        
        # If not in memory, try to reload from saved file
        # Look for files matching the dataset_id pattern
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.startswith(dataset_id):
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    try:
                        if filename.endswith('.csv'):
                            df = pd.read_csv(filepath)
                        elif filename.endswith(('.xlsx', '.xls')):
                            df = pd.read_excel(filepath)
                        else:
                            continue
                        
                        # Reload into memory for future use
                        datasets[dataset_id] = {
                            'name': filename.replace(f'{dataset_id}_', ''),
                            'data': df.to_dict('records'),
                            'columns': df.columns.tolist(),
                            'filepath': filepath
                        }
                        return df
                    except Exception as e:
                        raise ValueError(f'Error loading dataset file: {str(e)}')
        
        raise ValueError(f'Dataset not found: {dataset_id}. It may have been cleared from memory. Please re-upload the dataset.')


def _primary_column(columns):
    """Primary column for single-variable charts; backward compat."""
    return columns.get('column') if columns else None


def _apply_filters(df, filters):
    """Apply row-level filters: list of {column, operator, value}."""
    if not filters:
        return df
    for f in filters:
        col = f.get('column')
        op = f.get('operator', '=')
        val = f.get('value', '')
        if not col or col not in df.columns or val == '':
            continue
        try:
            col_s = df[col].astype(str)
            num_col = pd.to_numeric(df[col], errors='coerce')
            if op == '=':
                df = df[col_s == str(val)]
            elif op == '!=':
                df = df[col_s != str(val)]
            elif op == 'contains':
                df = df[col_s.str.contains(str(val), case=False, na=False)]
            elif op == 'not contains':
                df = df[~col_s.str.contains(str(val), case=False, na=False)]
            elif op == '>' and not num_col.isna().all():
                df = df[num_col > float(val)]
            elif op == '>=' and not num_col.isna().all():
                df = df[num_col >= float(val)]
            elif op == '<' and not num_col.isna().all():
                df = df[num_col < float(val)]
            elif op == '<=' and not num_col.isna().all():
                df = df[num_col <= float(val)]
        except Exception:
            pass
    return df


def _apply_date_group(df, column, date_group):
    """Group a date column by year/quarter/month/week/day. Returns (df, new_col_name)."""
    if not date_group or date_group == 'none' or column not in df.columns:
        return df, column
    try:
        df = df.copy()
        dt = pd.to_datetime(df[column], errors='coerce')
        if dt.isna().all():
            return df, column
        new_col = f'_dg_{date_group}'
        if date_group == 'year':
            df[new_col] = dt.dt.year.astype(str)
        elif date_group == 'quarter':
            df[new_col] = dt.dt.to_period('Q').astype(str)
        elif date_group == 'month':
            df[new_col] = dt.dt.to_period('M').astype(str)
        elif date_group == 'week':
            df[new_col] = dt.dt.to_period('W').apply(lambda r: str(r.start_time.date()) if hasattr(r, 'start_time') else str(r))
        elif date_group == 'day':
            df[new_col] = dt.dt.date.astype(str)
        return df, new_col
    except Exception:
        return df, column


def _get_value_counts(df, column, customization):
    """Shared helper: get (labels, values) with filters, date grouping, aggregation, top N, sort."""
    if not column:
        return [], []
    # Row-level filters
    df = _apply_filters(df, customization.get('filters') or [])
    # Date grouping
    date_group = customization.get('date_group')
    if date_group and date_group != 'none':
        df, column = _apply_date_group(df, column, date_group)
    # Legacy category filter
    selected = customization.get('selected_values') or []
    if selected:
        sel = [str(v).strip() for v in selected]
        df = df[df[column].astype(str).str.strip().isin(sel)]
        if len(df) == 0:
            raise ValueError(f'No data for selected categories: {selected}')
    # Aggregation
    agg_column = customization.get('agg_column')
    agg_func = customization.get('agg_func', 'count')
    if agg_column and agg_column in df.columns and agg_func != 'count':
        grouped = df.groupby(column)[agg_column]
        if agg_func == 'sum':
            result = grouped.sum()
        elif agg_func == 'mean':
            result = grouped.mean().round(2)
        elif agg_func == 'min':
            result = grouped.min()
        elif agg_func == 'max':
            result = grouped.max()
        else:
            result = grouped.count()
    else:
        result = df[column].value_counts()
    # Sort order
    sort_order = customization.get('sort_order', 'desc')
    if sort_order == 'asc':
        result = result.sort_values(ascending=True)
    elif sort_order == 'desc':
        result = result.sort_values(ascending=False)
    # else 'none' = keep natural order
    # Top N
    top_n = customization.get('top_n')
    if top_n and str(top_n).isdigit() and int(top_n) > 0:
        result = result.head(int(top_n))
    return result.index.tolist(), result.values.tolist()


def _base_layout(customization, title, show_legend=True):
    """Shared layout dict for charts. Applies Canva-style options: title (text, font, color, align), legend, fonts."""
    w = customization.get('width', 800)
    h = customization.get('height', 600)
    font_family = customization.get('font_family', 'Arial')
    font_size = int(customization.get('font_size', 12))
    title_font_color = customization.get('title_font_color', '#1a1a1a')
    title_x = customization.get('title_x', 0.5)
    title_y = customization.get('title_y', 1.0)
    title_anchor = customization.get('title_anchor', 'auto')
    xanchor = 'center'
    if title_anchor == 'left':
        xanchor = 'left'
    elif title_anchor == 'right':
        xanchor = 'right'
    layout = {
        'title': {
            'text': customization.get('title') or title,
            'font': dict(family=font_family, size=font_size + 4, color=title_font_color),
            'x': title_x,
            'y': title_y,
            'xanchor': xanchor,
        },
        'margin': dict(l=50, r=50, t=60, b=50),
        'width': w,
        'height': h,
        'showlegend': show_legend and customization.get('show_legend', True),
        'font': dict(family=font_family, size=font_size, color=customization.get('font_color', '#1a1a1a')),
        'xaxis': {
            'tickangle': -45,
            'tickfont': dict(family=font_family, size=font_size - 1),
            **({'title': {'text': customization['axis_title_x']}} if customization.get('axis_title_x') else {}),
        },
        'yaxis': {
            'tickfont': dict(family=font_family, size=font_size - 1),
            **({'title': {'text': customization['axis_title_y']}} if customization.get('axis_title_y') else {}),
        },
        'paper_bgcolor': customization.get('paper_bgcolor'),
        'plot_bgcolor': customization.get('plot_bgcolor'),
    }
    # Strip None values so Plotly uses defaults
    layout['title'] = {k: v for k, v in layout['title'].items() if v is not None}
    if layout.get('paper_bgcolor') is None:
        del layout['paper_bgcolor']
    if layout.get('plot_bgcolor') is None:
        del layout['plot_bgcolor']
    # Dark mode
    if customization.get('dark_mode'):
        layout['paper_bgcolor'] = '#1a1a2e'
        layout['plot_bgcolor'] = '#16213e'
        layout['font']['color'] = '#e0e0e0'
        layout['title']['font']['color'] = '#ffffff'
        layout['xaxis']['tickfont']['color'] = '#c0c0c0'
        layout['yaxis']['tickfont']['color'] = '#c0c0c0'
        if 'legend' in layout:
            layout['legend']['font']['color'] = '#e0e0e0'
    # Legend position and style
    legend_pos = customization.get('legend_position', 'right')
    if layout['showlegend'] and legend_pos and legend_pos != 'none':
        layout['legend'] = {
            'orientation': 'v' if legend_pos in ('left', 'right') else 'h',
            'x': 1.02 if legend_pos == 'right' else (-0.1 if legend_pos == 'left' else 0.5),
            'y': 1 if legend_pos == 'top' else (-0.1 if legend_pos == 'bottom' else 0.5),
            'xanchor': 'left' if legend_pos == 'right' else ('right' if legend_pos == 'left' else 'center'),
            'yanchor': 'top' if legend_pos == 'top' else ('bottom' if legend_pos == 'bottom' else 'middle'),
            'font': dict(family=font_family, size=int(customization.get('legend_font_size', font_size))),
        }
        if customization.get('legend_title'):
            layout['legend']['title'] = dict(text=customization['legend_title'])
    return layout


def _default_colors(n):
    return ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'] * (n // 8 + 1)


def _get_colors(n, customization, labels=None):
    """Use individual_colors (label->color), else customization['colors'], else default palette."""
    ind = customization.get('individual_colors') or {}
    if labels and ind:
        return [ind.get(str(lbl), _default_colors(n)[i] if i < n else '#888') for i, lbl in enumerate(labels[:n])]
    custom = customization.get('colors') or []
    if len(custom) >= n:
        return list(custom)[:n]
    return _default_colors(n)[:n]


def _add_reference_lines(fig, customization):
    """Add horizontal/vertical reference lines from customization."""
    ref_lines = customization.get('reference_lines') or []
    for rl in ref_lines:
        val = rl.get('value')
        label = rl.get('label', '')
        orientation = rl.get('orientation', 'h')
        color = rl.get('color', '#e63946')
        if val is None:
            continue
        try:
            val = float(val)
        except (ValueError, TypeError):
            continue
        if orientation == 'h':
            fig.add_hline(y=val, line_dash='dash', line_color=color,
                          annotation_text=label, annotation_position='top right')
        else:
            fig.add_vline(x=val, line_dash='dash', line_color=color,
                          annotation_text=label, annotation_position='top right')


def _add_trendline(fig, x_vals, y_vals, customization):
    """Add a linear trendline trace."""
    if not customization.get('show_trendline'):
        return
    try:
        import numpy as np
        x_num = list(range(len(x_vals)))
        y_num = [float(v) for v in y_vals]
        coeffs = np.polyfit(x_num, y_num, 1)
        trend_y = [coeffs[0] * i + coeffs[1] for i in x_num]
        fig.add_trace(go.Scatter(x=x_vals, y=trend_y, mode='lines',
                                 name='Trend', line=dict(dash='dot', color='#ff7c43', width=2)))
    except Exception:
        pass


def _fig_to_chart_response(fig, chart_type):
    return {'type': chart_type, 'data': json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)), 'preview_url': None}


def generate_pie_chart(df, columns, customization):
    column = _primary_column(columns)
    """Generate pie chart data"""
    # Apply filter if specified
    selected_values = customization.get('selected_values', None)
    
    if selected_values is not None and len(selected_values) > 0:
        # Convert selected_values to strings for comparison (remove whitespace)
        selected_values_str = [str(v).strip() for v in selected_values]
        
        # Get unique values from the column (also strip whitespace for comparison)
        column_values_str = df[column].astype(str).str.strip()
        
        # Filter dataframe to only include selected values
        mask = column_values_str.isin(selected_values_str)
        df_filtered = df[mask].copy()
        
        if len(df_filtered) == 0:
            available = df[column].unique().tolist()
            raise ValueError(f'No data found for selected categories: {selected_values}. Available categories: {available}')
        
        # Use filtered dataframe
        df = df_filtered
    
    # Count values in the column (only selected categories will be here if filter was applied)
    value_counts = df[column].value_counts()
    
    # If filter was applied, ensure only selected categories appear
    if selected_values is not None and len(selected_values) > 0:
        selected_values_str = [str(v).strip() for v in selected_values]
        # Filter value_counts to only include selected categories
        value_counts = value_counts[value_counts.index.astype(str).str.strip().isin(selected_values_str)]
    
    # Get customization options
    colors = customization.get('colors', None)
    individual_colors = customization.get('individual_colors', {})  # Dict mapping label to color
    font_family = customization.get('font_family', 'Arial')
    font_size = customization.get('font_size', 12)
    title = customization.get('title', f'Pie Chart: {column}')
    width = customization.get('width', 800)
    height = customization.get('height', 600)
    width_enabled = customization.get('width_enabled', True)
    height_enabled = customization.get('height_enabled', True)
    title_x = customization.get('title_x', 0.5)  # 0 to 1
    title_y = customization.get('title_y', 1.0)  # 0 to 1
    title_anchor = customization.get('title_anchor', 'auto')  # 'auto', 'left', 'center', 'right'
    
    # Legend options
    show_legend = customization.get('show_legend', True)
    legend_title = customization.get('legend_title', '')
    legend_position = customization.get('legend_position', 'right')  # 'right', 'left', 'top', 'bottom', 'none'
    legend_x = customization.get('legend_x', None)
    legend_y = customization.get('legend_y', None)
    
    # Tooltip options
    show_tooltip = customization.get('show_tooltip', True)
    tooltip_template = customization.get('tooltip_template', '<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>')
    
    # Prepare colors array - use individual colors if provided, otherwise use general colors
    final_colors = []
    labels = value_counts.index.tolist()
    if individual_colors:
        # Use individual colors mapping
        for label in labels:
            final_colors.append(individual_colors.get(str(label), '#cccccc'))
    elif colors and len(colors) >= len(value_counts):
        final_colors = colors[:len(value_counts)]
    else:
        # Default colors
        default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        final_colors = default_colors[:len(value_counts)]
    
    # Create Plotly figure with tooltip
    hover_template = tooltip_template if show_tooltip else None
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=value_counts.values.tolist(),
        textinfo='label+percent',
        textfont=dict(family=font_family, size=font_size),
        marker=dict(colors=final_colors),
        hovertemplate=hover_template
    )])
    
    # Prepare layout
    layout_dict = {
        'title': dict(
            text=title,
            font=dict(family=font_family, size=font_size + 4),
            x=title_x,
            y=title_y,
            xanchor=title_anchor,
            pad=dict(t=20, b=10)  # Add padding to prevent truncation
        ),
        'font': dict(family=font_family, size=font_size),
        'autosize': not (width_enabled or height_enabled),
        'margin': dict(l=50, r=50, t=100, b=50)  # Add margins to prevent cutoff
    }
    
    # Add dimensions only if enabled
    if width_enabled:
        layout_dict['width'] = width
    if height_enabled:
        layout_dict['height'] = height
    
    # Legend configuration
    if show_legend and legend_position != 'none':
        legend_dict = {
            'orientation': 'v' if legend_position in ['left', 'right'] else 'h',
            'x': legend_x if legend_x is not None else (1.02 if legend_position == 'right' else (-0.1 if legend_position == 'left' else 0.5)),
            'y': legend_y if legend_y is not None else (1 if legend_position == 'top' else (-0.1 if legend_position == 'bottom' else 0.5)),
            'xanchor': 'left' if legend_position == 'right' else ('right' if legend_position == 'left' else 'center'),
            'yanchor': 'top' if legend_position == 'top' else ('bottom' if legend_position == 'bottom' else 'middle'),
            'title': dict(text=legend_title) if legend_title else None,
            'font': dict(family=font_family, size=font_size)
        }
        layout_dict['showlegend'] = True
        layout_dict['legend'] = legend_dict
    else:
        layout_dict['showlegend'] = False
    
    # Update layout with all customization options
    fig.update_layout(**layout_dict)
    
    # Convert to JSON
    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    return {
        'type': 'pie',
        'data': json.loads(graph_json),
        'preview_url': None  # Will be generated on frontend
    }


def generate_bar_chart(df, columns, customization):
    column = _primary_column(columns)
    group_by = customization.get('group_by')
    show_labels = customization.get('show_data_labels', True)
    text_pos = 'auto' if show_labels else 'none'
    title = customization.get('title', f'Bar Chart: {column}')
    # Apply row filters + date group before groupby
    df = _apply_filters(df, customization.get('filters') or [])
    date_group = customization.get('date_group')
    if date_group and date_group != 'none':
        df, column = _apply_date_group(df, column, date_group)
    if group_by and group_by in df.columns and group_by != column:
        series = df[group_by].dropna().unique().tolist()
        colors = _get_colors(len(series), customization)
        traces = []
        for i, s in enumerate(series):
            sub = df[df[group_by] == s]
            sub_cust = dict(customization)
            sub_cust['filters'] = []  # already filtered
            sub_cust['date_group'] = 'none'
            lbls, vals = _get_value_counts(sub, column, sub_cust)
            traces.append(go.Bar(name=str(s), x=lbls, y=vals,
                                 marker_color=colors[i % len(colors)],
                                 text=vals if show_labels else None,
                                 textposition=text_pos))
        fig = go.Figure(data=traces)
        barmode = 'stack' if customization.get('bar_mode') == 'stack' else 'group'
        layout = _base_layout(customization, title)
        layout['barmode'] = barmode
        fig.update_layout(**layout)
    else:
        labels, values = _get_value_counts(df, column, customization)
        colors = _get_colors(len(labels), customization, labels)
        fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color=colors,
                                     text=values if show_labels else None, textposition=text_pos)])
        _add_trendline(fig, labels, values, customization)
        fig.update_layout(**_base_layout(customization, title))
    _add_reference_lines(fig, customization)
    return _fig_to_chart_response(fig, 'bar')


def generate_line_chart(df, columns, customization):
    column = _primary_column(columns)
    group_by = customization.get('group_by')
    title = customization.get('title', f'Line Chart: {column}')
    df = _apply_filters(df, customization.get('filters') or [])
    date_group = customization.get('date_group')
    if date_group and date_group != 'none':
        df, column = _apply_date_group(df, column, date_group)
    if group_by and group_by in df.columns and group_by != column:
        series = df[group_by].dropna().unique().tolist()
        colors = _get_colors(len(series), customization)
        traces = []
        for i, s in enumerate(series):
            sub = df[df[group_by] == s]
            sub_cust = dict(customization); sub_cust['filters'] = []; sub_cust['date_group'] = 'none'
            lbls, vals = _get_value_counts(sub, column, sub_cust)
            traces.append(go.Scatter(name=str(s), x=lbls, y=vals, mode='lines+markers',
                                     line=dict(width=2, color=colors[i % len(colors)]), marker=dict(size=8)))
        fig = go.Figure(data=traces)
        fig.update_layout(**_base_layout(customization, title))
    else:
        labels, values = _get_value_counts(df, column, customization)
        fig = go.Figure(data=[go.Scatter(x=labels, y=values, mode='lines+markers', line=dict(width=2), marker=dict(size=10))])
        _add_trendline(fig, labels, values, customization)
        fig.update_layout(**_base_layout(customization, title))
    _add_reference_lines(fig, customization)
    return _fig_to_chart_response(fig, 'line')


def generate_scatter_chart(df, columns, customization):
    x_col = columns.get('x_column')
    y_col = columns.get('y_column')
    size_col = columns.get('size_column')
    df = _apply_filters(df, customization.get('filters') or [])
    if x_col and y_col and x_col in df.columns and y_col in df.columns:
        df_clean = df[[x_col, y_col]].dropna()
        if size_col and size_col in df.columns:
            df_clean = df[[x_col, y_col, size_col]].dropna()
            sizes = (df_clean[size_col] - df_clean[size_col].min()) / (df_clean[size_col].max() - df_clean[size_col].min() + 0.1) * 30 + 5
            sizes = sizes.tolist()
        else:
            sizes = 12
        title = customization.get('title', f'Scatter: {x_col} vs {y_col}')
        fig = go.Figure(data=[go.Scatter(x=df_clean[x_col], y=df_clean[y_col], mode='markers', marker=dict(size=sizes))])
        _add_trendline(fig, df_clean[x_col].tolist(), df_clean[y_col].tolist(), customization)
    else:
        column = _primary_column(columns)
        labels, values = _get_value_counts(df, column, customization)
        title = customization.get('title', f'Scatter: {column}')
        fig = go.Figure(data=[go.Scatter(x=labels, y=values, mode='markers', marker=dict(size=12))])
        _add_trendline(fig, labels, values, customization)
    _add_reference_lines(fig, customization)
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'scatter')


def generate_area_chart(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Area Chart: {column}')
    fig = go.Figure(data=[go.Scatter(x=labels, y=values, fill='tozeroy', line=dict(width=2))])
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'area')


def generate_donut_chart(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Donut Chart: {column}')
    colors = _get_colors(len(labels), customization, labels)
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4, marker=dict(colors=colors), textinfo='label+percent')])
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'donut')


def generate_horizontal_bar(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Horizontal Bar: {column}')
    colors = _get_colors(len(labels), customization, labels)
    show_labels = customization.get('show_data_labels', True)
    fig = go.Figure(data=[go.Bar(x=values, y=labels, orientation='h', marker_color=colors,
                                  text=values if show_labels else None, textposition='auto')])
    _add_reference_lines(fig, customization)
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'horizontal_bar')


def generate_stacked_bar(df, columns, customization):
    column = _primary_column(columns)
    group_by = customization.get('group_by')
    title = customization.get('title', f'Stacked Bar: {column}')
    show_labels = customization.get('show_data_labels', True)
    df = _apply_filters(df, customization.get('filters') or [])
    if group_by and group_by in df.columns and group_by != column:
        series = df[group_by].dropna().unique().tolist()
        colors = _get_colors(len(series), customization)
        traces = []
        for i, s in enumerate(series):
            sub = df[df[group_by] == s]
            sub_cust = dict(customization); sub_cust['filters'] = []
            lbls, vals = _get_value_counts(sub, column, sub_cust)
            traces.append(go.Bar(name=str(s), x=lbls, y=vals, marker_color=colors[i % len(colors)],
                                 text=vals if show_labels else None, textposition='auto'))
        fig = go.Figure(data=traces)
        fig.update_layout(**_base_layout(customization, title), barmode='stack')
    else:
        labels, values = _get_value_counts(df, column, customization)
        colors = _get_colors(len(labels), customization, labels)
        fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color=colors,
                                     text=values if show_labels else None, textposition='auto')])
        fig.update_layout(**_base_layout(customization, title), barmode='stack')
    _add_reference_lines(fig, customization)
    return _fig_to_chart_response(fig, 'stacked_bar')


def generate_grouped_bar(df, columns, customization):
    result = generate_bar_chart(df, columns, customization)
    result['type'] = 'grouped_bar'
    return result


def generate_line_marker(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Line with Markers: {column}')
    fig = go.Figure(data=[go.Scatter(x=labels, y=values, mode='lines+markers', marker=dict(size=14), line=dict(width=2))])
    _add_trendline(fig, labels, values, customization)
    _add_reference_lines(fig, customization)
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'line_marker')


def generate_area_stacked(df, columns, customization):
    return generate_area_chart(df, columns, customization)  # single series = same as area


def generate_histogram(df, columns, customization):
    column = _primary_column(columns)
    title = customization.get('title', f'Histogram: {column}')
    fig = go.Figure(data=[go.Histogram(x=df[column].dropna(), nbinsx=min(30, max(10, len(df[column].unique()))) )])
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'histogram')


def generate_box_chart(df, columns, customization):
    column = _primary_column(columns)
    title = customization.get('title', f'Box Plot: {column}')
    fig = go.Figure(data=[go.Box(y=df[column].dropna(), name=column)])
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'box')


def generate_heatmap(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Heatmap: {column}')
    # 1-row heatmap: categories vs counts
    fig = go.Figure(data=go.Heatmap(z=[values], x=labels, y=['Count'], colorscale='Blues', showscale=True))
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'heatmap')


def generate_treemap(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Treemap: {column}')
    fig = go.Figure(go.Treemap(labels=labels, values=values, parents=[''] * len(labels)))
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'treemap')


def generate_sunburst(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Sunburst: {column}')
    fig = go.Figure(go.Sunburst(labels=labels, values=values, parents=[''] * len(labels)))
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'sunburst')


def generate_funnel(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Funnel: {column}')
    fig = go.Figure(go.Funnel(name=column, y=labels, x=values))
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'funnel')


def generate_radar(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Radar: {column}')
    n = len(labels)
    if n < 3:
        labels = list(labels) + [''] * (3 - n)
        values = list(values) + [0] * (3 - n)
        n = 3
    fig = go.Figure(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]], fill='toself'))
    fig.update_layout(**_base_layout(customization, title), polar=dict(radialaxis=dict(visible=True)))
    return _fig_to_chart_response(fig, 'radar')


def generate_polar_area(df, columns, customization):
    column = _primary_column(columns)
    labels, values = _get_value_counts(df, column, customization)
    title = customization.get('title', f'Polar Area: {column}')
    colors = _get_colors(len(labels), customization, labels)
    fig = go.Figure(go.Barpolar(r=values, theta=labels, marker_color=colors))
    fig.update_layout(**_base_layout(customization, title), polar=dict(radialaxis=dict(visible=True)))
    return _fig_to_chart_response(fig, 'polar_area')


def generate_bubble(df, columns, customization):
    x_col = columns.get('x_column')
    y_col = columns.get('y_column')
    size_col = columns.get('size_column')
    if x_col and y_col and x_col in df.columns and y_col in df.columns:
        df_clean = df[[x_col, y_col]].dropna()
        if size_col and size_col in df.columns:
            df_clean = df[[x_col, y_col, size_col]].dropna()
            sizes = (df_clean[size_col] - df_clean[size_col].min()) / (df_clean[size_col].max() - df_clean[size_col].min() + 0.1) * 40 + 8
            sizes = sizes.tolist()
        else:
            sizes = 15
        title = customization.get('title', f'Bubble: {x_col} vs {y_col}')
        fig = go.Figure(go.Scatter(x=df_clean[x_col], y=df_clean[y_col], mode='markers', marker=dict(size=sizes), text=df_clean.index.tolist(), hovertemplate=f'{x_col}: %{{x}}<br>{y_col}: %{{y}}<extra></extra>'))
    else:
        column = _primary_column(columns)
        labels, values = _get_value_counts(df, column, customization)
        title = customization.get('title', f'Bubble: {column}')
        sizes = [v * 3 + 10 for v in values]
        fig = go.Figure(go.Scatter(x=range(len(labels)), y=values, mode='markers', marker=dict(size=sizes), text=labels, hovertemplate='%{text}: %{y}<extra></extra>'))
    fig.update_layout(**_base_layout(customization, title))
    return _fig_to_chart_response(fig, 'bubble')


# Chart type id -> generator (for named types only; chart_type_21..100 stay unimplemented)
CHART_GENERATORS = {
    'pie': generate_pie_chart,
    'bar': generate_bar_chart,
    'line': generate_line_chart,
    'scatter': generate_scatter_chart,
    'area': generate_area_chart,
    'donut': generate_donut_chart,
    'horizontal_bar': generate_horizontal_bar,
    'stacked_bar': generate_stacked_bar,
    'grouped_bar': generate_grouped_bar,
    'line_marker': generate_line_marker,
    'area_stacked': generate_area_stacked,
    'histogram': generate_histogram,
    'box': generate_box_chart,
    'heatmap': generate_heatmap,
    'treemap': generate_treemap,
    'sunburst': generate_sunburst,
    'funnel': generate_funnel,
    'radar': generate_radar,
    'polar_area': generate_polar_area,
    'bubble': generate_bubble,
}


def map_font_to_r_family(font_name):
    """Map common font names to R-compatible font families"""
    font_mapping = {
        'Arial': 'sans',
        'Helvetica': 'sans',
        'Verdana': 'sans',
        'Times New Roman': 'serif',
        'Times': 'serif',
        'Courier New': 'mono',
        'Courier': 'mono',
        'Georgia': 'serif',
        'Palatino': 'serif',
        'Garamond': 'serif',
        'Comic Sans MS': 'sans',
        'Trebuchet MS': 'sans',
        'Impact': 'sans',
        'Lucida Console': 'mono',
        'Lucida Sans Unicode': 'sans',
        'Tahoma': 'sans',
        'Century Gothic': 'sans'
    }
    
    # Return mapped font or default to sans
    return font_mapping.get(font_name, 'sans')

def generate_r_code(chart_type, df, columns, customization, dataset_id=None):
    """Generate R code for the chart - reads from data source. Uses first available column for multi-variable charts."""
    column = _primary_column(columns)
    if not column and columns:
        column = next((v for v in columns.values() if v), None)
    if not column:
        raise ValueError('No column specified for R code export.')
    individual_colors = customization.get('individual_colors', {})
    colors = customization.get('colors', ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
    font_family_input = customization.get('font_family', 'Arial')
    font_family = map_font_to_r_family(font_family_input)  # Map to R-compatible name
    font_size = customization.get('font_size', 12)
    title = customization.get('title', f'Pie Chart: {column}')
    width = customization.get('width', 800)
    height = customization.get('height', 600)
    width_enabled = customization.get('width_enabled', True)
    height_enabled = customization.get('height_enabled', True)
    title_x = customization.get('title_x', 0.5)
    
    # Legend options
    show_legend = customization.get('show_legend', True)
    legend_title = customization.get('legend_title', '')
    legend_position = customization.get('legend_position', 'right')
    
    # Tooltip options
    show_tooltip = customization.get('show_tooltip', True)
    
    # Filter options
    selected_values = customization.get('selected_values', None)
    
    # Get dataset file path
    dataset_path = None
    if dataset_id:
        if dataset_id.startswith('sample_'):
            filename = dataset_id.replace('sample_', '')
            dataset_path = os.path.join(DATASETS_FOLDER, filename)
        else:
            if dataset_id in datasets and 'filepath' in datasets[dataset_id]:
                dataset_path = datasets[dataset_id]['filepath']
    
    # Get unique values for color mapping
    value_counts = df[column].value_counts()
    labels = value_counts.index.tolist()
    
    # Build label code for showing values/percentages on chart
    # Calculate positions for labels - add after data preparation
    # For pie charts, we need to calculate the angle and position for each slice
    pie_data_label_code = '''
# Calculate label positions and percentages for pie chart
pie_data <- pie_data %>%
    arrange(desc(value)) %>%
    mutate(
        percentage = round(value / sum(value) * 100, 1),
        label = paste0(category, "\\n", value, " (", percentage, "%)"),
        # Calculate cumulative percentages for positioning
        cumsum_value = cumsum(value),
        ymax = cumsum_value,
        ymin = c(0, head(ymax, n = -1)),
        # Position label at the middle of each slice
        label_y = (ymax + ymin) / 2
    )'''
    
    # Prepare colors - use individual colors if provided
    if individual_colors:
        color_mapping = []
        for label in labels:
            color = individual_colors.get(str(label), '#cccccc')
            color_mapping.append(f'"{label}" = "{color}"')
        color_values = ',\n        '.join(color_mapping)
        scale_fill_code = f'scale_fill_manual(values = c(\n        {color_values}\n    ))'
    else:
        color_list = ', '.join([f'"{c}"' for c in colors[:len(value_counts)]])
        scale_fill_code = f'scale_fill_manual(values = c({color_list}))'
    
    # Determine data source code
    if dataset_path:
        # Use file path
        file_ext = os.path.splitext(dataset_path)[1].lower()
        # Convert Windows path to R-friendly format
        r_path = dataset_path.replace('\\', '/')
        # Escape column name if it contains spaces or special characters
        column_escaped = f"`{column}`" if ' ' in column or '-' in column else column
        
        # Build filter code if values are selected
        filter_code = ''
        if selected_values and len(selected_values) > 0:
            # Convert selected values to R vector format
            values_list = ', '.join([f'"{str(v)}"' for v in selected_values])
            filter_code = f'''
# Filter data to include only selected categories
data <- data %>%
    filter({column_escaped} %in% c({values_list}))'''
        
        if file_ext == '.csv':
            data_source_code = f'''# Read data from CSV file
# Note: Update the file path below to match your data file location
data <- read.csv("{r_path}", stringsAsFactors = FALSE){filter_code}

# Prepare data for pie chart (counting occurrences of each category)
pie_data <- data %>%
    count({column_escaped}) %>%
    rename(category = {column_escaped}, value = n){pie_data_label_code}'''
        elif file_ext in ['.xlsx', '.xls']:
            data_source_code = f'''# Read data from Excel file
# Note: Update the file path below to match your data file location
data <- read_excel("{r_path}"){filter_code}

# Prepare data for pie chart (counting occurrences of each category)
pie_data <- data %>%
    count({column_escaped}) %>%
    rename(category = {column_escaped}, value = n){pie_data_label_code}'''
        else:
            # Fallback to hardcoded
            data_source_code = f'''# Data
pie_data <- data.frame(
    category = c({', '.join([f'"{val}"' for val in labels])}),
    value = c({', '.join([str(val) for val in value_counts.values])})
){pie_data_label_code}'''
    else:
        # Fallback to hardcoded if no file path
        data_source_code = f'''# Data
pie_data <- data.frame(
    category = c({', '.join([f'"{val}"' for val in labels])}),
    value = c({', '.join([str(val) for val in value_counts.values])})
){pie_data_label_code}'''
    
    # Calculate title hjust from title_x (0=left, 0.5=center, 1=right)
    hjust = title_x
    
    # Calculate dimensions in inches (assuming 100 DPI conversion)
    width_inches = width / 100 if width_enabled else None
    height_inches = height / 100 if height_enabled else None
    
    # Determine which packages are needed
    packages_needed = ['ggplot2', 'dplyr']
    if dataset_path and os.path.splitext(dataset_path)[1].lower() in ['.xlsx', '.xls']:
        packages_needed.append('readxl')
    
    # Add plotly and htmlwidgets for tooltips if needed
    if show_tooltip:
        packages_needed.append('plotly')
        packages_needed.append('htmlwidgets')
    
    # Create package installation code
    package_install_code = f"""# Install required packages if not already installed
required_packages <- c({', '.join([f'"{pkg}"' for pkg in packages_needed])})

for (pkg in required_packages) {{
    if (!require(pkg, character.only = TRUE)) {{
        install.packages(pkg, dependencies = TRUE)
        library(pkg, character.only = TRUE)
    }}
}}"""
    
    # Build library loading section
    library_load_code = '\n'.join([f'library({pkg})' for pkg in packages_needed])
    
    # Font handling comment
    font_comment = f"""# Font Note: Using R's built-in font family "{font_family}" (mapped from "{font_family_input}")
# R font families: "sans" (Arial-like), "serif" (Times-like), "mono" (Courier-like)
# For custom Windows fonts, install and load the 'extrafont' package:
#   install.packages("extrafont")
#   library(extrafont)
#   font_import()  # Run once to import Windows fonts
#   loadfonts(device = "win")  # Load fonts for Windows
# Then use: family = "{font_family_input}" (exact font name)"""
    
    # Build legend code
    legend_pos = legend_position if show_legend and legend_position != 'none' else 'none'
    legend_labs = f' + labs(fill = "{legend_title}")' if show_legend and legend_title else ''
    
    # Build tooltip code - add interactive tooltips if enabled
    tooltip_code = ''
    if show_tooltip:
        tooltip_code = '''

# Convert to interactive plotly chart with tooltips
# This creates an interactive HTML widget with hover tooltips showing category, value, and percentage
pie_chart_interactive <- plotly::ggplotly(pie_chart, tooltip = "text")
print(pie_chart_interactive)

# Save interactive chart as HTML file (open in browser to see tooltips)
htmlwidgets::saveWidget(pie_chart_interactive, "pie_chart_interactive.html", selfcontained = TRUE)'''
    
    # Build save code
    if width_inches and height_inches:
        save_png = f'ggsave("pie_chart.png", pie_chart, width = {width_inches}, height = {height_inches}, dpi = 300)'
        save_pdf = f'ggsave("pie_chart.pdf", pie_chart, width = {width_inches}, height = {height_inches})'
    else:
        save_png = 'ggsave("pie_chart.png", pie_chart, dpi = 300)'
        save_pdf = 'ggsave("pie_chart.pdf", pie_chart)'
    
    r_code = f"""# Pie Chart: {title}
# Generated by Charts Generator

{package_install_code}

# Load required libraries (already loaded by installation code above, but included for clarity)
{library_load_code}

{data_source_code}

{font_comment}

# Create pie chart{(' with tooltip support' if show_tooltip else '')}
pie_chart <- ggplot(pie_data, aes(x = "", y = value, fill = category{', text = paste0("Category: ", category, "\\nValue: ", value, "\\nPercentage: ", round(value/sum(value)*100, 1), "%")' if show_tooltip else ''})) +
    geom_bar(stat = "identity", width = 1) +
    geom_text(aes(y = label_y, label = label), 
              color = "white", 
              fontface = "bold",
              size = {max(font_size / 3, 2.5)},
              family = "{font_family}",
              show.legend = FALSE,
              inherit.aes = TRUE) +
    coord_polar("y", start = 0) +
    {scale_fill_code} +
    labs(title = "{title}"){legend_labs} +
    theme_void() +
    theme(
        plot.title = element_text(family = "{font_family}", size = {font_size + 4}, hjust = {hjust}),
        legend.text = element_text(family = "{font_family}", size = {font_size}),
        legend.title = element_text(family = "{font_family}", size = {font_size + 2}),
        legend.position = "{legend_pos}"
    )

# Display chart
print(pie_chart){tooltip_code}

# Save as PNG
{save_png}

# Save as PDF
{save_pdf}
"""
    
    return r_code

def generate_python_code(chart_type, df, columns, customization, dataset_id=None):
    """Generate Python/matplotlib code for the chart."""
    column = _primary_column(columns)
    if not column and columns:
        column = next((v for v in columns.values() if v), None)
    if not column:
        raise ValueError('No column specified for Python code export.')

    colors = customization.get('colors', ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'])
    individual_colors = customization.get('individual_colors', {})
    font_size = customization.get('font_size', 12)
    title = customization.get('title', f'{chart_type.replace("_", " ").title()}: {column}')
    width = customization.get('width', 800)
    height = customization.get('height', 600)
    dark_mode = customization.get('dark_mode', False)
    agg_column = customization.get('agg_column')
    agg_func = customization.get('agg_func', 'count')

    # Dataset loading code
    dataset_path = None
    if dataset_id:
        if dataset_id.startswith('sample_'):
            filename = dataset_id.replace('sample_', '')
            dataset_path = os.path.join(DATASETS_FOLDER, filename)
        elif dataset_id in datasets and 'filepath' in datasets[dataset_id]:
            dataset_path = datasets[dataset_id]['filepath']

    col_ref = f'"{column}"'
    if dataset_path:
        r_path = dataset_path.replace('\\', '/')
        ext = os.path.splitext(dataset_path)[1].lower()
        if ext == '.csv':
            load_code = f'df = pd.read_csv("{r_path}")'
        elif ext in ['.xlsx', '.xls']:
            load_code = f'df = pd.read_excel("{r_path}")'
        else:
            load_code = '# df = pd.read_csv("your_file.csv")  # load your data here'
    else:
        load_code = '# df = pd.read_csv("your_file.csv")  # load your data here'

    # Aggregation / data preparation
    if agg_column and agg_func != 'count':
        data_prep = f'data = df.groupby({col_ref})["{agg_column}"].{agg_func}().sort_values(ascending=False)\nlabels = data.index.tolist()\nvalues = data.values.tolist()'
        y_label = f'{agg_func.title()} of {agg_column}'
    else:
        data_prep = f'data = df[{col_ref}].value_counts()\nlabels = data.index.tolist()\nvalues = data.values.tolist()'
        y_label = 'Count'

    # Colors
    value_counts = df[column].value_counts()
    labels_list = value_counts.index.tolist()
    n = len(labels_list)
    if individual_colors:
        final_colors = [individual_colors.get(str(lbl), colors[i % len(colors)]) for i, lbl in enumerate(labels_list)]
    else:
        final_colors = [colors[i % len(colors)] for i in range(n)]
    color_line = f'colors = {repr(final_colors[:n])}'

    w_in = round(width / 100, 1)
    h_in = round(height / 100, 1)
    style_line = 'plt.style.use("dark_background")' if dark_mode else ''

    x_col = columns.get('x_column', column)
    y_col = columns.get('y_column', column)

    if chart_type == 'pie':
        chart_code = f'''{color_line}
wedge_props = dict(edgecolor='white', linewidth=1.5)
ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, wedgeprops=wedge_props)
ax.axis('equal')'''
    elif chart_type == 'donut':
        chart_code = f'''{color_line}
wedge_props = dict(edgecolor='white', linewidth=1.5)
ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90,
       wedgeprops=wedge_props, pctdistance=0.75)
centre_circle = plt.Circle((0, 0), 0.5, fc='white')
ax.add_patch(centre_circle)
ax.axis('equal')'''
    elif chart_type in ('bar', 'grouped_bar', 'stacked_bar'):
        chart_code = f'''{color_line}
ax.bar(labels, values, color=colors, edgecolor='white', linewidth=0.5)
ax.set_xlabel('{column}')
ax.set_ylabel('{y_label}')
plt.xticks(rotation=45, ha='right')
ax.yaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)'''
    elif chart_type == 'horizontal_bar':
        chart_code = f'''{color_line}
ax.barh(labels, values, color=colors, edgecolor='white', linewidth=0.5)
ax.set_xlabel('{y_label}')
ax.set_ylabel('{column}')
ax.xaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)'''
    elif chart_type in ('line', 'line_marker'):
        marker = "'o'" if chart_type == 'line_marker' else 'None'
        chart_code = f'''ax.plot(labels, values, marker={marker}, linewidth=2, markersize=8)
ax.set_xlabel('{column}')
ax.set_ylabel('{y_label}')
plt.xticks(rotation=45, ha='right')
ax.yaxis.grid(True, linestyle='--', alpha=0.7)'''
    elif chart_type in ('area', 'area_stacked'):
        chart_code = f'''ax.fill_between(range(len(labels)), values, alpha=0.4)
ax.plot(range(len(labels)), values, linewidth=2)
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45, ha='right')
ax.set_ylabel('{y_label}')
ax.yaxis.grid(True, linestyle='--', alpha=0.7)'''
    elif chart_type == 'histogram':
        chart_code = f'''ax.hist(df[{col_ref}].dropna(), bins=30, color="{final_colors[0] if final_colors else '#1f77b4'}", edgecolor='white')
ax.set_xlabel('{column}')
ax.set_ylabel('Frequency')
ax.yaxis.grid(True, linestyle='--', alpha=0.7)'''
    elif chart_type == 'box':
        chart_code = f'''ax.boxplot(df[{col_ref}].dropna(), patch_artist=True,
           boxprops=dict(facecolor="{final_colors[0] if final_colors else '#1f77b4'}", alpha=0.7))
ax.set_ylabel('{column}')
ax.yaxis.grid(True, linestyle='--', alpha=0.7)'''
    elif chart_type in ('scatter', 'bubble'):
        chart_code = f'''ax.scatter(df["{x_col}"], df["{y_col}"], alpha=0.7, color="{final_colors[0] if final_colors else '#1f77b4'}")
ax.set_xlabel('{x_col}')
ax.set_ylabel('{y_col}')
ax.grid(True, linestyle='--', alpha=0.5)'''
    else:
        chart_code = f'''{color_line}
ax.bar(labels, values, color=colors)
ax.set_xlabel('{column}')
ax.set_ylabel('{y_label}')
plt.xticks(rotation=45, ha='right')'''

    python_code = f'''# {title}
# Generated by Charts Generator

import pandas as pd
import matplotlib.pyplot as plt

# --- Load data ---
{load_code}

# --- Prepare data ---
{data_prep}

# --- Plot ---
{style_line + chr(10) if style_line else ''}fig, ax = plt.subplots(figsize=({w_in}, {h_in}))

{chart_code}

ax.set_title("{title}", fontsize={font_size + 4}, fontweight='bold', pad=12)
plt.tight_layout()
plt.savefig("chart.png", dpi=150, bbox_inches='tight')
plt.savefig("chart.pdf", bbox_inches='tight')
plt.show()
'''
    return python_code


def generate_svg(chart_type, df, columns, customization):
    """Generate SVG string."""
    fig = generate_plotly_figure(chart_type, df, columns, customization)
    return fig.to_image(format='svg').decode('utf-8')


def generate_png(chart_type, df, columns, customization):
    """Generate PNG image"""
    fig = generate_plotly_figure(chart_type, df, columns, customization)
    
    # Get custom dimensions or use defaults
    width = customization.get('width', 1200) if customization.get('width_enabled', True) else None
    height = customization.get('height', 800) if customization.get('height_enabled', True) else None
    
    # Convert to PNG using kaleido
    if width and height:
        img_bytes = fig.to_image(format="png", width=width, height=height)
    else:
        img_bytes = fig.to_image(format="png")
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return img_base64

def generate_pdf(chart_type, df, columns, customization):
    """Generate PDF"""
    fig = generate_plotly_figure(chart_type, df, columns, customization)
    
    # Get custom dimensions or use defaults
    width = customization.get('width', 1200) if customization.get('width_enabled', True) else None
    height = customization.get('height', 800) if customization.get('height_enabled', True) else None
    
    # Convert to PNG first
    if width and height:
        img_bytes = fig.to_image(format="png", width=width, height=height)
    else:
        img_bytes = fig.to_image(format="png")
        # Use default dimensions for PDF if not specified
        width = width or 1200
        height = height or 800
    
    # Create PDF
    buffer = BytesIO()
    # Use custom dimensions for PDF page size
    page_width = max(width, letter[0])
    page_height = max(height, letter[1])
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    # Add image to PDF
    img = ImageReader(BytesIO(img_bytes))
    c.drawImage(img, 0, 0, width=width, height=height)
    c.save()
    
    pdf_bytes = buffer.getvalue()
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    return pdf_base64

def generate_html(chart_type, df, columns, customization):
    """Generate standalone HTML file"""
    fig = generate_plotly_figure(chart_type, df, columns, customization)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{customization.get('title', 'Chart')}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div id="chart"></div>
    <script>
        var figure = {json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)};
        Plotly.newPlot('chart', figure.data, figure.layout);
    </script>
</body>
</html>"""
    
    return html_content

def generate_plotly_figure(chart_type, df, columns, customization):
    """Generate Plotly figure for export (PNG/PDF/HTML). Use CHART_GENERATORS when available."""
    if chart_type in CHART_GENERATORS:
        result = CHART_GENERATORS[chart_type](df, columns, customization)
        return go.Figure(result['data'])
    column = _primary_column(columns)
    if chart_type == 'pie' and column:
        # Apply filter if specified
        selected_values = customization.get('selected_values', None)
        if selected_values and len(selected_values) > 0:
            # Convert selected_values to strings for comparison
            selected_values_str = [str(v) for v in selected_values]
            # Filter dataframe to only include selected values
            df = df[df[column].astype(str).isin(selected_values_str)]
            if len(df) == 0:
                raise ValueError(f'No data found for selected categories: {selected_values}')
        
        value_counts = df[column].value_counts()
        colors = customization.get('colors', None)
        individual_colors = customization.get('individual_colors', {})
        font_family = customization.get('font_family', 'Arial')
        font_size = customization.get('font_size', 12)
        title = customization.get('title', f'Pie Chart: {column}')
        width = customization.get('width', 800)
        height = customization.get('height', 600)
        width_enabled = customization.get('width_enabled', True)
        height_enabled = customization.get('height_enabled', True)
        title_x = customization.get('title_x', 0.5)
        title_y = customization.get('title_y', 1.0)
        title_anchor = customization.get('title_anchor', 'auto')
        
        # Legend options
        show_legend = customization.get('show_legend', True)
        legend_title = customization.get('legend_title', '')
        legend_position = customization.get('legend_position', 'right')
        legend_x = customization.get('legend_x', None)
        legend_y = customization.get('legend_y', None)
        
        # Tooltip options
        show_tooltip = customization.get('show_tooltip', True)
        tooltip_template = customization.get('tooltip_template', '<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>')
        
        # Prepare colors array
        final_colors = []
        labels = value_counts.index.tolist()
        if individual_colors:
            for label in labels:
                final_colors.append(individual_colors.get(str(label), '#cccccc'))
        elif colors and len(colors) >= len(value_counts):
            final_colors = colors[:len(value_counts)]
        else:
            default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
            final_colors = default_colors[:len(value_counts)]
        
        hover_template = tooltip_template if show_tooltip else None
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=value_counts.values.tolist(),
            textinfo='label+percent',
            textfont=dict(family=font_family, size=font_size),
            marker=dict(colors=final_colors),
            hovertemplate=hover_template
        )])
        
        # Prepare layout
        layout_dict = {
            'title': dict(
                text=title,
                font=dict(family=font_family, size=font_size + 4),
                x=title_x,
                y=title_y,
                xanchor=title_anchor
            ),
            'font': dict(family=font_family, size=font_size),
            'autosize': not (width_enabled or height_enabled)
        }
        
        # Add dimensions only if enabled
        if width_enabled:
            layout_dict['width'] = width
        if height_enabled:
            layout_dict['height'] = height
        
        # Legend configuration
        if show_legend and legend_position != 'none':
            legend_dict = {
                'orientation': 'v' if legend_position in ['left', 'right'] else 'h',
                'x': legend_x if legend_x is not None else (1.02 if legend_position == 'right' else (-0.1 if legend_position == 'left' else 0.5)),
                'y': legend_y if legend_y is not None else (1 if legend_position == 'top' else (-0.1 if legend_position == 'bottom' else 0.5)),
                'xanchor': 'left' if legend_position == 'right' else ('right' if legend_position == 'left' else 'center'),
                'yanchor': 'top' if legend_position == 'top' else ('bottom' if legend_position == 'bottom' else 'middle'),
                'font': dict(family=font_family, size=font_size)
            }
            if legend_title:
                legend_dict['title'] = dict(text=legend_title)
            layout_dict['showlegend'] = True
            layout_dict['legend'] = legend_dict
        else:
            layout_dict['showlegend'] = False
        
        # Add margins to prevent title/label truncation
        if 'margin' not in layout_dict:
            layout_dict['margin'] = dict(l=50, r=50, t=100, b=50)
        
        # Ensure title has padding
        if 'title' in layout_dict and isinstance(layout_dict['title'], dict):
            if 'pad' not in layout_dict['title']:
                layout_dict['title']['pad'] = dict(t=20, b=10)
        
        # Update layout with all customization options
        fig.update_layout(**layout_dict)
        
        return fig

@app.route('/api/datasets/<dataset_id>/stats', methods=['GET'])
def get_dataset_stats(dataset_id):
    """Get per-column statistics (min/max/mean/nulls/unique)."""
    try:
        df = load_dataset(dataset_id)
        stats = {}
        for col in df.columns:
            s = {
                'type': str(df[col].dtype),
                'nulls': int(df[col].isna().sum()),
                'null_pct': round(df[col].isna().mean() * 100, 1),
                'unique': int(df[col].nunique()),
            }
            if pd.api.types.is_numeric_dtype(df[col]):
                s['min'] = round(float(df[col].min()), 4) if not df[col].isna().all() else None
                s['max'] = round(float(df[col].max()), 4) if not df[col].isna().all() else None
                s['mean'] = round(float(df[col].mean()), 4) if not df[col].isna().all() else None
                s['median'] = round(float(df[col].median()), 4) if not df[col].isna().all() else None
            stats[col] = s
        return jsonify({'stats': stats, 'row_count': len(df), 'col_count': len(df.columns)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    index_path = os.path.join(FRONTEND_FOLDER, 'index.html')
    index_abs = os.path.abspath(index_path)
    print("=" * 60)
    print("Charts Generator — Backend")
    print("=" * 60)
    print("Serving frontend from this file:")
    print("  ", index_abs)
    print("Upload folder:     ", os.path.abspath(UPLOAD_FOLDER))
    print("Sample datasets:   ", os.path.abspath(DATASETS_FOLDER))
    print("")
    print("Open in browser:   http://localhost:5000")
    print("You should see a green bar at the top: 'App version: 2025-02-fresh'")
    print("=" * 60)
    app.run(debug=True, port=5000, host='127.0.0.1')
