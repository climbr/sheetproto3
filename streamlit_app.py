import streamlit as st
import pandas as pd
import io
from datetime import datetime, date

# Page config
st.set_page_config(
    page_title="Test Case Manager",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern, compact CSS styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        font-size: 1.8rem;
        margin: 0;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }
    
    .compact-form {
        background: #ffffff;
        border: 1px solid #e8ecef;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    .form-section {
        margin-bottom: 1rem;
    }
    
    .form-section h4 {
        color: #2d3748;
        font-size: 1rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.25rem;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-passed { background: #10b981; color: white; }
    .status-failed { background: #ef4444; color: white; }
    .status-pending { background: #f59e0b; color: white; }
    .status-blocked { background: #6b7280; color: white; }
    
    .success-alert {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
    }
    
    .changes-summary {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-size: 0.85rem;
        text-align: center;
    }
    
    .filter-info {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        color: #0369a1;
        padding: 0.5rem;
        border-radius: 6px;
        font-size: 0.8rem;
        text-align: center;
    }
    
    .navigation-compact {
        background: #f8fafc;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .test-header {
        background: linear-gradient(135deg, #1f2937, #374151);
        color: white;
        padding: 1rem;
        border-radius: 12px 12px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .test-header h2 {
        margin: 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    /* Compact form inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        padding: 0.5rem !important;
        font-size: 0.9rem !important;
        border-radius: 6px !important;
    }
    
    .stTextArea > div > div > textarea {
        min-height: 60px !important;
    }
    
    /* Compact buttons */
    .stButton > button {
        padding: 0.5rem 1rem !important;
        font-size: 0.85rem !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'filtered_indices' not in st.session_state:
        st.session_state.filtered_indices = []
    if 'current_position' not in st.session_state:
        st.session_state.current_position = 0
    if 'changes_log' not in st.session_state:
        st.session_state.changes_log = {}
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None
    if 'last_save_message' not in st.session_state:
        st.session_state.last_save_message = None
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = 'All'
    if 'selected_status' not in st.session_state:
        st.session_state.selected_status = 'All'

def load_csv(uploaded_file):
    """Load and process CSV file"""
    df = pd.read_csv(uploaded_file)
    
    expected_columns = [
        'ID', 'Category', 'Test Case', 'Test Description', 'Test Input', 
        'Expected Outcome', 'Test Env', 'Observed Outcome', 'Test Status', 
        'Date of Last Test', 'Notes'
    ]
    
    for col in expected_columns:
        if col not in df.columns:
            df[col] = ''
    
    df = df[expected_columns].fillna('')
    return df

def apply_filters():
    """Apply current filters and update filtered_indices"""
    if st.session_state.df is None:
        st.session_state.filtered_indices = []
        return
    
    df = st.session_state.df
    filtered_indices = []
    
    for idx, row in df.iterrows():
        if (st.session_state.selected_category != 'All' and 
            str(row['Category']) != st.session_state.selected_category):
            continue
        
        if (st.session_state.selected_status != 'All' and 
            str(row['Test Status']) != st.session_state.selected_status):
            continue
        
        filtered_indices.append(idx)
    
    st.session_state.filtered_indices = filtered_indices
    
    if st.session_state.current_position >= len(filtered_indices):
        st.session_state.current_position = max(0, len(filtered_indices) - 1)

def get_current_test_index():
    """Get the actual dataframe index of the current test case"""
    if (not st.session_state.filtered_indices or 
        st.session_state.current_position >= len(st.session_state.filtered_indices)):
        return 0
    return st.session_state.filtered_indices[st.session_state.current_position]

def track_change(field, old_value, new_value, test_case_id):
    """Track changes made to test cases"""
    if str(old_value) != str(new_value):
        change_key = f"{test_case_id}_{field}"
        st.session_state.changes_log[change_key] = {
            'test_case_id': test_case_id,
            'field': field,
            'old_value': str(old_value),
            'new_value': str(new_value),
            'timestamp': datetime.now().isoformat()
        }
        return True
    return False

def save_changes_to_dataframe(current_test_idx, form_data, test_id):
    """Save all form changes to the dataframe - THIS IS THE KEY FIX"""
    current_test = st.session_state.df.iloc[current_test_idx].copy()
    changes_made = 0
    changed_fields = []
    
    # Define the mapping of form fields to dataframe columns
    field_mapping = {
        'Category': form_data['category'],
        'Test Case': form_data['test_case'], 
        'Test Description': form_data['description'],
        'Test Input': form_data['test_input'],
        'Expected Outcome': form_data['expected'],
        'Test Env': form_data['env'],
        'Test Status': form_data['status'],
        'Date of Last Test': str(form_data['date']),
        'Observed Outcome': form_data['observed'],
        'Notes': form_data['notes']
    }
    
    # Track changes and update dataframe
    for field, new_value in field_mapping.items():
        old_value = current_test.get(field, '')
        if track_change(field, old_value, new_value, test_id):
            changes_made += 1
            changed_fields.append(field)
        
        # CRITICAL: Actually update the dataframe
        st.session_state.df.at[current_test_idx, field] = new_value
    
    return changes_made, changed_fields

def export_data():
    """Export current dataframe with changes to CSV"""
    if st.session_state.df is not None:
        # Ensure we're exporting the current state
        csv_buffer = io.StringIO()
        st.session_state.df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue()
    return None

def main():
    initialize_session_state()
    
    # Compact header
    st.markdown("""
    <div class="main-header">
        <h1>🧪 Test Case Manager</h1>
        <p>Efficient test case management with focused navigation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📁 File Upload")
        uploaded_file = st.file_uploader("Upload CSV", type="csv", label_visibility="collapsed")
        
        if uploaded_file is not None:
            try:
                df = load_csv(uploaded_file)
                if st.session_state.df is None or not df.equals(st.session_state.df):
                    st.session_state.df = df.copy()
                    st.session_state.original_df = df.copy()
                    st.session_state.current_position = 0
                    st.session_state.changes_log = {}
                    st.session_state.last_save_message = None
                    apply_filters()
                
                st.success(f"✅ {len(df)} test cases loaded")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                return
        
        # Compact filters
        if st.session_state.df is not None:
            st.markdown("### 🔍 Filters")
            
            categories = ['All'] + sorted([cat for cat in st.session_state.df['Category'].unique() 
                                         if cat and str(cat).strip()])
            new_category = st.selectbox("Category", categories, 
                                      index=categories.index(st.session_state.selected_category) 
                                      if st.session_state.selected_category in categories else 0,
                                      label_visibility="collapsed")
            
            statuses = ['All'] + sorted([status for status in st.session_state.df['Test Status'].unique() 
                                       if status and str(status).strip()])
            new_status = st.selectbox("Status", statuses,
                                    index=statuses.index(st.session_state.selected_status) 
                                    if st.session_state.selected_status in statuses else 0,
                                    label_visibility="collapsed")
            
            # Update filters
            if (new_category != st.session_state.selected_category or 
                new_status != st.session_state.selected_status):
                st.session_state.selected_category = new_category
                st.session_state.selected_status = new_status
                st.session_state.current_position = 0
                apply_filters()
                st.rerun()
            
            # Filter status
            if (st.session_state.selected_category != 'All' or 
                st.session_state.selected_status != 'All'):
                st.markdown(f"""
                <div class="filter-info">
                    📊 {len(st.session_state.filtered_indices)} of {len(st.session_state.df)} cases
                </div>
                """, unsafe_allow_html=True)
        
        # Compact navigation
        if st.session_state.df is not None and st.session_state.filtered_indices:
            st.markdown("### 🧭 Navigation")
            
            total_filtered = len(st.session_state.filtered_indices)
            current_num = st.session_state.current_position + 1
            
            st.markdown(f"""
            <div class="navigation-compact">
                <center><strong>{current_num} of {total_filtered}</strong></center>
            </div>
            """, unsafe_allow_html=True)
            
            if total_filtered > 1:
                progress = st.session_state.current_position / max(1, total_filtered - 1)
                st.progress(progress)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("◀ Prev", disabled=st.session_state.current_position == 0, use_container_width=True):
                    st.session_state.current_position -= 1
                    st.session_state.last_save_message = None
                    st.rerun()
            
            with col2:
                if st.button("Next ▶", disabled=st.session_state.current_position >= total_filtered - 1, use_container_width=True):
                    st.session_state.current_position += 1
                    st.session_state.last_save_message = None
                    st.rerun()
        
        # Changes summary
        if st.session_state.changes_log:
            st.markdown("### 📊 Changes")
            changes_count = len(st.session_state.changes_log)
            affected_tests = len(set(change['test_case_id'] for change in st.session_state.changes_log.values()))
            
            st.markdown(f"""
            <div class="changes-summary">
                <strong>{changes_count}</strong> changes<br>
                <strong>{affected_tests}</strong> test cases modified
            </div>
            """, unsafe_allow_html=True)
        
        # Export
        if st.session_state.df is not None:
            st.markdown("### 💾 Export")
            csv_data = export_data()
            if csv_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                changes_count = len(st.session_state.changes_log)
                filename = f"tests_{changes_count}changes_{timestamp}.csv" if changes_count > 0 else f"tests_{timestamp}.csv"
                
                st.download_button(
                    label=f"⬇️ Download ({changes_count} changes)",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True
                )
    
    # Main content
    if st.session_state.df is not None and st.session_state.filtered_indices:
        current_test_idx = get_current_test_index()
        current_test = st.session_state.df.iloc[current_test_idx].copy()
        test_id = current_test.get('ID', current_test_idx)
        
        # Success message
        if st.session_state.last_save_message:
            st.markdown(f"""
            <div class="success-alert">
                {st.session_state.last_save_message}
            </div>
            """, unsafe_allow_html=True)
        
        # Test header
        current_status = current_test.get('Test Status', 'Pending')
        status_class = f"status-{current_status.lower()}" if current_status else "status-pending"
        
        st.markdown(f"""
        <div class="test-header">
            <h2>Test Case {test_id}</h2>
            <span class="status-badge {status_class}">{current_status}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact form
        with st.form(key=f"form_{current_test_idx}", clear_on_submit=False):
            st.markdown('<div class="compact-form">', unsafe_allow_html=True)
            
            # Basic info
            st.markdown('<div class="form-section"><h4>📋 Basic Information</h4></div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                category = st.text_input("Category", value=str(current_test.get('Category', '')), label_visibility="collapsed", placeholder="Category")
                test_case = st.text_input("Test Case", value=str(current_test.get('Test Case', '')), label_visibility="collapsed", placeholder="Test Case Name")
            with col2:
                env = st.text_input("Environment", value=str(current_test.get('Test Env', '')), label_visibility="collapsed", placeholder="Test Environment")
                status = st.selectbox("Status", ['Pending', 'Passed', 'Failed', 'Blocked'], 
                                    index=['Pending', 'Passed', 'Failed', 'Blocked'].index(current_status) if current_status in ['Pending', 'Passed', 'Failed', 'Blocked'] else 0,
                                    label_visibility="collapsed")
            
            # Test details
            st.markdown('<div class="form-section"><h4>📝 Test Details</h4></div>', unsafe_allow_html=True)
            description = st.text_area("Description", value=str(current_test.get('Test Description', '')), 
                                     height=80, label_visibility="collapsed", placeholder="Test Description")
            
            col1, col2 = st.columns(2)
            with col1:
                test_input = st.text_area("Input", value=str(current_test.get('Test Input', '')), 
                                        height=70, label_visibility="collapsed", placeholder="Test Input")
                expected = st.text_area("Expected", value=str(current_test.get('Expected Outcome', '')), 
                                      height=70, label_visibility="collapsed", placeholder="Expected Outcome")
            with col2:
                observed = st.text_area("Observed", value=str(current_test.get('Observed Outcome', '')), 
                                      height=70, label_visibility="collapsed", placeholder="Observed Outcome")
                notes = st.text_area("Notes", value=str(current_test.get('Notes', '')), 
                                    height=70, label_visibility="collapsed", placeholder="Notes")
            
            # Date
            current_date = current_test.get('Date of Last Test', '')
            if current_date and str(current_date).strip():
                try:
                    current_date = pd.to_datetime(current_date).date()
                except:
                    current_date = None
            else:
                current_date = None
            
            test_date = st.date_input("Test Date", value=current_date, label_visibility="collapsed")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Submit
            col1, col2 = st.columns([3, 1])
            with col1:
                submitted = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
            with col2:
                if st.session_state.current_position < len(st.session_state.filtered_indices) - 1:
                    save_next = st.form_submit_button("Save & Next ▶", use_container_width=True)
                else:
                    save_next = False
            
            if submitted or save_next:
                # Prepare form data
                form_data = {
                    'category': category,
                    'test_case': test_case,
                    'description': description,
                    'test_input': test_input,
                    'expected': expected,
                    'env': env,
                    'status': status,
                    'date': test_date,
                    'observed': observed,
                    'notes': notes
                }
                
                # Save changes to dataframe
                changes_made, changed_fields = save_changes_to_dataframe(current_test_idx, form_data, test_id)
                
                # Create success message
                if changes_made > 0:
                    fields_text = ', '.join(changed_fields)
                    st.session_state.last_save_message = f"✅ Saved {changes_made} change(s) to Test Case {test_id}: {fields_text}"
                else:
                    st.session_state.last_save_message = f"ℹ️ No changes detected for Test Case {test_id}"
                
                # Move to next if requested
                if save_next:
                    st.session_state.current_position += 1
                    st.session_state.last_save_message = None
                
                apply_filters()  # Reapply in case category/status changed
                st.rerun()
    
    elif st.session_state.df is not None and len(st.session_state.filtered_indices) == 0:
        st.warning("🔍 No test cases match the current filters.")
    elif st.session_state.df is not None:
        st.warning("📄 No test cases found in the uploaded file.")
    else:
        st.info("👆 Upload a CSV file to get started.")

if __name__ == "__main__":
    main()
