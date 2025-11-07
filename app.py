@app.route('/api/bulk-upload', methods=['POST'])
@require_auth
def bulk_upload():
    """Handle bulk upload of titles dengan improved error handling"""
    try:
        # Check if file is provided
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({"error": "No file selected"}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            logger.error(f"File type not allowed: {file.filename}")
            return jsonify({"error": "File type not allowed. Please upload CSV or TXT file"}), 400
        
        logger.info(f"Processing uploaded file: {file.filename}")
        
        titles = []
        keywords_map = {}
        
        # Process based on file type
        if file.filename.lower().endswith('.csv'):
            titles, keywords_map = process_csv_file(file)
            logger.info(f"CSV processing completed: {len(titles)} titles found")
            
        elif file.filename.lower().endswith('.txt'):
            titles, keywords_map = process_txt_file(file)
            logger.info(f"TXT processing completed: {len(titles)} titles found")
        
        else:
            return jsonify({"error": "Unsupported file format. Use CSV or TXT"}), 400
        
        # Validate that we got some titles
        if not titles:
            logger.warning("No valid titles found in uploaded file")
            return jsonify({"error": "No valid titles found in the file. Please check the file format."}), 400
        
        # Add titles to system
        count = auto_poster.add_bulk_titles(titles, keywords_map)
        
        logger.info(f"Bulk upload successful: {count} titles added")
        return jsonify({
            "success": True,
            "message": f"Successfully added {count} titles",
            "titles": titles[:10],  # Return first 10 titles for preview
            "count": count
        })
        
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_extensions = {'csv', 'txt'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def process_csv_file(file):
    """Process CSV file dengan improved error handling"""
    titles = []
    keywords_map = {}
    
    try:
        # Reset file pointer
        file.stream.seek(0)
        
        # Try different encodings
        content = None
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                file.stream.seek(0)
                content = file.read().decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            logger.error("Could not decode file with any encoding")
            return titles, keywords_map
        
        # Split into lines and process
        lines = content.splitlines()
        logger.info(f"CSV file has {len(lines)} lines")
        
        if not lines:
            return titles, keywords_map
        
        # Detect delimiter
        first_line = lines[0]
        delimiter = detect_delimiter(first_line)
        logger.info(f"Detected delimiter: {repr(delimiter)}")
        
        # Process CSV
        reader = csv.reader(lines, delimiter=delimiter)
        
        # Get headers
        try:
            headers = next(reader)
            logger.info(f"CSV headers: {headers}")
        except StopIteration:
            logger.error("CSV file is empty")
            return titles, keywords_map
        
        # Determine column indices
        title_index = 0  # Default to first column
        keyword_index = None
        
        # Try to find title and keyword columns
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            if any(keyword in header_lower for keyword in ['title', 'judul', 'post', 'article']):
                title_index = i
                logger.info(f"Title column found at index {i}: {header}")
            elif 'keyword' in header_lower:
                keyword_index = i
                logger.info(f"Keyword column found at index {i}: {header}")
        
        # Process rows
        for row_num, row in enumerate(reader, start=2):
            try:
                if not row:  # Skip empty rows
                    continue
                
                # Get title
                if len(row) > title_index:
                    title = row[title_index].strip()
                    if title:  # Only process non-empty titles
                        titles.append(title)
                        
                        # Get keywords if available
                        if keyword_index is not None and len(row) > keyword_index:
                            keyword_str = row[keyword_index].strip()
                            if keyword_str:
                                keywords = [k.strip() for k in keyword_str.split(',') if k.strip()]
                                keywords_map[title] = keywords
                                logger.debug(f"Row {row_num}: Title='{title}', Keywords={keywords}")
                            else:
                                logger.debug(f"Row {row_num}: Title='{title}', No keywords")
                        else:
                            logger.debug(f"Row {row_num}: Title='{title}'")
                    else:
                        logger.warning(f"Row {row_num}: Empty title, skipping")
                else:
                    logger.warning(f"Row {row_num}: No title column found")
                    
            except Exception as e:
                logger.warning(f"Error processing row {row_num}: {str(e)}")
                continue
        
        logger.info(f"CSV processing completed: {len(titles)} valid titles found")
        return titles, keywords_map
        
    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}", exc_info=True)
        return titles, keywords_map

def process_txt_file(file):
    """Process TXT file dengan improved error handling"""
    titles = []
    
    try:
        # Reset file pointer
        file.stream.seek(0)
        
        # Try different encodings
        content = None
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                file.stream.seek(0)
                content = file.read().decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            logger.error("Could not decode TXT file with any encoding")
            return titles, {}
        
        # Process each line
        lines = content.split('\n')
        logger.info(f"TXT file has {len(lines)} lines")
        
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if line and not line.startswith('#'):  # Skip empty lines and comments
                titles.append(line)
                logger.debug(f"Line {line_num}: '{line}'")
        
        logger.info(f"TXT processing completed: {len(titles)} valid titles found")
        return titles, {}
        
    except Exception as e:
        logger.error(f"Error processing TXT file: {str(e)}", exc_info=True)
        return titles, {}

def detect_delimiter(first_line):
    """Detect CSV delimiter from first line"""
    delimiters = [',', ';', '\t', '|']
    max_count = 0
    best_delimiter = ','
    
    for delimiter in delimiters:
        count = first_line.count(delimiter)
        if count > max_count:
            max_count = count
            best_delimiter = delimiter
    
    return best_delimiter
