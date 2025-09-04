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

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .test-case-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .status-passed {
        background-color: #d4edda;
        color: #155724;
        padding: 0.25rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    
    .status-failed {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.25rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    
    .status-pending {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    
    .status-blocked {
        background-color: #e2e3e5;
        color: #383d41;
        padding: 0.25rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    
    .navigation-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 1rem 0;
        padding: 1rem;
        background: #e9ecef;
        border-radius: 10px;
    }
    
    .changes-summary {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .success-message {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    
    .filter-info {
        background: #e7f3ff;
        border: 1px solid #b3d4fc;
        color: #004085;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'filtered_indices' not in st.session_state:
        st.session_state.filtered_indices = []
    if 'current_position' not in st.session_state:  # Position in filtered list
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
    
    # Ensure all expected columns exist
    expected_columns = [
        'ID', 'Category', 'Test Case', 'Test Description', 'Test Input', 
        'Expected Outcome', 'Test Env', 'Observed Outcome', 'Test Status', 
        'Date of Last Test', 'Notes'
    ]
    
    for col in expected_columns:
        if col not in df.columns:
            df[col] = ''
    
    # Fill NaN values with empty strings
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
        # Category filter
        if (st.session_state.selected_category != 'All' and 
            str(row['Category']) != st.session_state.selected_category):
            continue
        
        # Status filter
        if (st.session_state.selected_status != 'All' and 
            str(row['Test Status']) != st.session_state.selected_status):
            continue
        
        filtered_indices.append(idx)
    
    st.session_state.filtered_indices = filtered_indices
    
    # Reset position if current position is out of bounds
    if st.session_state.current_position >= len(filtered_indices):
        st.session_state.current_position = max(0, len(filtered_indices) - 1)

def get_current_test_index():
    """Get the actual dataframe index of the current test case"""
    if (not st.session_state.filtered_indices or 
        st.session_state.current_position >= len(st.session_state.filtered_indices)):
        return 0
    return st.session_state.filtered_indices[st.session_state.current_position]

def get_status_class(status):
    """Get CSS class for status styling"""
    if pd.isna(status) or status == '':
        return 'status-pending'
    status_lower = str(status).lower()
    if 'pass' in status_lower:
        return 'status-passed'
    elif 'fail' in status_lower:
        return 'status-failed'
    elif 'block' in status_lower:
        return 'status-blocked'
    else:
        return 'status-pending'

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

def get_changes_summary():
    """Get summary of all changes made"""
    if not st.session_state.changes_log:
        return None
    
    changes_by_test = {}
    for change in st.session_state.changes_log.values():
        tc_id = change['test_case_id']
        if tc_id not in changes_by_test:
            changes_by_test[tc_id] = []
        changes_by_test[tc_id].append(change)
    
    return changes_by_test

def export_data():
    """Export current dataframe with changes to CSV"""
    if st.session_state.df is not None:
        csv_buffer = io.StringIO()
        st.session_state.df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue()
    return None

def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧪 Test Case Manager</h1>
        <p>Focus on one test case at a time for efficient manual testing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for file upload and navigation
    with st.sidebar:
        st.header("📁 File Management")
        
        uploaded_file = st.file_uploader(
            "Upload CSV File", 
            type="csv",
            help="Upload your test cases CSV file"
        )
        
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
                
                st.success(f"✅ Loaded {len(df)} test cases")
                
            except Exception as e:
                st.error(f"Error loading CSV: {str(e)}")
                return
        
        # Filter Controls
        if st.session_state.df is not None:
            st.header("🔍 Filters")
            
            # Category filter
            categories = ['All'] + sorted([cat for cat in st.session_state.df['Category'].unique() 
                                         if cat and str(cat).strip()])
            new_category = st.selectbox("Filter by Category:", categories, 
                                      index=categories.index(st.session_state.selected_category) 
                                      if st.session_state.selected_category in categories else 0)
            
            # Status filter
            statuses = ['All'] + sorted([status for status in st.session_state.df['Test Status'].unique() 
                                       if status and str(status).strip()])
            new_status = st.selectbox("Filter by Status:", statuses,
                                    index=statuses.index(st.session_state.selected_status) 
                                    if st.session_state.selected_status in statuses else 0)
            
            # Check if filters changed
            if (new_category != st.session_state.selected_category or 
                new_status != st.session_state.selected_status):
                st.session_state.selected_category = new_category
                st.session_state.selected_status = new_status
                st.session_state.current_position = 0  # Reset to first filtered item
                apply_filters()
                st.rerun()
            
            # Show filter status
            if (st.session_state.selected_category != 'All' or 
                st.session_state.selected_status != 'All'):
                filter_text = f"Filtered: {len(st.session_state.filtered_indices)} of {len(st.session_state.df)} test cases"
                st.markdown(f'<div class="filter-info">{filter_text}</div>', 
                           unsafe_allow_html=True)
        
        # Navigation controls
        if st.session_state.df is not None and st.session_state.filtered_indices:
            st.header("🧭 Navigation")
            
            total_filtered = len(st.session_state.filtered_indices)
            current_position_display = st.session_state.current_position + 1
            
            st.write(f"**Test Case {current_position_display} of {total_filtered}**")
            
            # Progress bar
            if total_filtered > 1:
                progress = st.session_state.current_position / max(1, total_filtered - 1)
                st.progress(progress)
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Previous", disabled=st.session_state.current_position == 0):
                    st.session_state.current_position = max(0, st.session_state.current_position - 1)
                    st.session_state.last_save_message = None  # Clear save message
                    st.rerun()
            
            with col2:
                if st.button("Next ➡️", disabled=st.session_state.current_position >= total_filtered - 1):
                    st.session_state.current_position = min(total_filtered - 1, st.session_state.current_position + 1)
                    st.session_state.last_save_message = None  # Clear save message
                    st.rerun()
            
            # Jump to specific test case
            if total_filtered > 1:
                st.write("**Jump to Test Case:**")
                jump_options = []
                for i, actual_idx in enumerate(st.session_state.filtered_indices):
                    test_row = st.session_state.df.iloc[actual_idx]
                    test_name = str(test_row['Test Case'])[:30]
                    if len(str(test_row['Test Case'])) > 30:
                        test_name += "..."
                    jump_options.append(f"#{i+1}: {test_name}")
                
                selected_jump = st.selectbox(
                    "Select test case:",
                    options=range(total_filtered),
                    index=st.session_state.current_position,
                    format_func=lambda x: jump_options[x]
                )
                
                if selected_jump != st.session_state.current_position:
                    st.session_state.current_position = selected_jump
                    st.session_state.last_save_message = None
                    st.rerun()
        
        # Changes Summary
        if st.session_state.changes_log:
            st.header("📊 Changes Summary")
            changes_summary = get_changes_summary()
            total_changes = len(st.session_state.changes_log)
            affected_tests = len(changes_summary) if changes_summary else 0
            
            st.markdown(f"""
            <div class="changes-summary">
                <strong>{total_changes}</strong> changes made<br>
                <strong>{affected_tests}</strong> test cases modified
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔍 View All Changes"):
                st.session_state.show_changes_detail = True
        
        # Export section
        if st.session_state.df is not None:
            st.header("💾 Export")
            
            csv_data = export_data()
            if csv_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                changes_count = len(st.session_state.changes_log)
                filename = f"test_cases_updated_{timestamp}.csv"
                if changes_count > 0:
                    filename = f"test_cases_{changes_count}changes_{timestamp}.csv"
                
                st.download_button(
                    label=f"⬇️ Download CSV ({changes_count} changes)",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help=f"Download your updated test cases with {changes_count} changes applied"
                )
    
    # Main content area
    if st.session_state.df is not None and st.session_state.filtered_indices:
        current_test_idx = get_current_test_index()
        current_test = st.session_state.df.iloc[current_test_idx].copy()
        test_id = current_test.get('ID', current_test_idx)
        
        # Show success message if available
        if st.session_state.last_save_message:
            st.markdown(f"""
            <div class="success-message">
                {st.session_state.last_save_message}
            </div>
            """, unsafe_allow_html=True)
        
        # Test case header with status
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.title(f"Test Case {current_test.get('ID', 'N/A')}")
        
        with col2:
            current_status = current_test.get('Test Status', 'Pending')
            status_class = get_status_class(current_status)
            st.markdown(f'<span class="{status_class}">{current_status}</span>', 
                       unsafe_allow_html=True)
        
        with col3:
            total_filtered = len(st.session_state.filtered_indices)
            if st.session_state.current_position < total_filtered - 1:
                if st.button("Save & Next ➡️", type="primary"):
                    st.session_state.current_position += 1
                    st.session_state.last_save_message = None
                    st.rerun()
        
        # Test case form
        with st.form(key=f"test_case_form_{current_test_idx}"):
            
            # Basic Information
            st.subheader("📋 Basic Information")
            col1, col2 = st.columns(2)
            
            with col1:
                new_category = st.text_input(
                    "Category", 
                    value=str(current_test.get('Category', '')),
                    key=f"category_{current_test_idx}"
                )
            
            with col2:
                new_test_case = st.text_input(
                    "Test Case Name", 
                    value=str(current_test.get('Test Case', '')),
                    key=f"test_case_{current_test_idx}"
                )
            
            # Test Details
            st.subheader("🔍 Test Details")
            new_description = st.text_area(
                "Test Description", 
                value=str(current_test.get('Test Description', '')),
                height=100,
                key=f"description_{current_test_idx}"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                new_test_input = st.text_area(
                    "Test Input", 
                    value=str(current_test.get('Test Input', '')),
                    height=80,
                    key=f"input_{current_test_idx}"
                )
            
            with col2:
                new_expected = st.text_area(
                    "Expected Outcome", 
                    value=str(current_test.get('Expected Outcome', '')),
                    height=80,
                    key=f"expected_{current_test_idx}"
                )
            
            # Test Environment
            st.subheader("🌐 Test Environment")
            new_env = st.text_input(
                "Test Environment", 
                value=str(current_test.get('Test Env', '')),
                key=f"env_{current_test_idx}"
            )
            
            # Test Results
            st.subheader("✅ Test Results")
            col1, col2 = st.columns(2)
            
            with col1:
                status_options = ['Pending', 'Passed', 'Failed', 'Blocked']
                current_status_value = str(current_test.get('Test Status', 'Pending'))
                if current_status_value not in status_options:
                    status_options.append(current_status_value)
                
                new_status = st.selectbox(
                    "Test Status",
                    options=status_options,
                    index=status_options.index(current_status_value),
                    key=f"status_{current_test_idx}"
                )
            
            with col2:
                current_date = current_test.get('Date of Last Test', '')
                if current_date and str(current_date).strip():
                    try:
                        current_date = pd.to_datetime(current_date).date()
                    except:
                        current_date = None
                else:
                    current_date = None
                
                new_date = st.date_input(
                    "Date of Last Test", 
                    value=current_date,
                    key=f"date_{current_test_idx}"
                )
            
            new_observed = st.text_area(
                "Observed Outcome", 
                value=str(current_test.get('Observed Outcome', '')),
                height=100,
                key=f"observed_{current_test_idx}"
            )
            
            # Notes
            st.subheader("📝 Notes")
            new_notes = st.text_area(
                "Notes", 
                value=str(current_test.get('Notes', '')),
                height=80,
                key=f"notes_{current_test_idx}"
            )
            
            # Form submission
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
            
            if submitted:
                # Track all changes and count them
                changes_made = 0
                changed_fields = []
                
                if track_change('Category', current_test.get('Category', ''), new_category, test_id):
                    changes_made += 1
                    changed_fields.append('Category')
                if track_change('Test Case', current_test.get('Test Case', ''), new_test_case, test_id):
                    changes_made += 1
                    changed_fields.append('Test Case')
                if track_change('Test Description', current_test.get('Test Description', ''), new_description, test_id):
                    changes_made += 1
                    changed_fields.append('Description')
                if track_change('Test Input', current_test.get('Test Input', ''), new_test_input, test_id):
                    changes_made += 1
                    changed_fields.append('Test Input')
                if track_change('Expected Outcome', current_test.get('Expected Outcome', ''), new_expected, test_id):
                    changes_made += 1
                    changed_fields.append('Expected Outcome')
                if track_change('Test Env', current_test.get('Test Env', ''), new_env, test_id):
                    changes_made += 1
                    changed_fields.append('Environment')
                if track_change('Test Status', current_test.get('Test Status', ''), new_status, test_id):
                    changes_made += 1
                    changed_fields.append('Status')
                if track_change('Date of Last Test', current_test.get('Date of Last Test', ''), str(new_date), test_id):
                    changes_made += 1
                    changed_fields.append('Date')
                if track_change('Observed Outcome', current_test.get('Observed Outcome', ''), new_observed, test_id):
                    changes_made += 1
                    changed_fields.append('Observed Outcome')
                if track_change('Notes', current_test.get('Notes', ''), new_notes, test_id):
                    changes_made += 1
                    changed_fields.append('Notes')
                
                # Update the dataframe
                st.session_state.df.iloc[current_test_idx] = [
                    test_id, new_category, new_test_case, new_description, new_test_input,
                    new_expected, new_env, new_observed, new_status, str(new_date), new_notes
                ]
                
                # Create success message
                if changes_made > 0:
                    fields_text = ', '.join(changed_fields)
                    st.session_state.last_save_message = f"✅ Successfully saved {changes_made} change(s) to Test Case {test_id}: {fields_text}"
                else:
                    st.session_state.last_save_message = f"ℹ️ No changes detected for Test Case {test_id}"
                
                # Reapply filters in case category or status changed
                apply_filters()
                st.rerun()
    
    elif st.session_state.df is not None and len(st.session_state.filtered_indices) == 0:
        st.warning("🔍 No test cases match the current filters. Try adjusting your filter criteria.")
        
    elif st.session_state.df is not None and len(st.session_state.df) == 0:
        st.warning("📄 No test cases found in the uploaded CSV file.")
    
    else:
        st.info("👆 Please upload a CSV file to get started.")
        
        # Show sample format
        with st.expander("📋 Expected CSV Format"):
            st.write("Your CSV should have these columns:")
            sample_data = {
                'ID': ['TC001', 'TC002'],
                'Category': ['Login', 'Navigation'],
                'Test Case': ['Valid Login', 'Menu Navigation'],
                'Test Description': ['Test login with valid credentials', 'Test main menu navigation'],
                'Test Input': ['username: admin, password: 123', 'Click on menu items'],
                'Expected Outcome': ['Successfully logged in', 'Menu items work correctly'],
                'Test Env': ['Chrome, Windows 10', 'Firefox, MacOS'],
                'Observed Outcome': ['', ''],
                'Test Status': ['Pending', 'Pending'],
                'Date of Last Test': ['', ''],
                'Notes': ['', '']
            }
            st.dataframe(pd.DataFrame(sample_data))
    
    # Show detailed changes if requested
    if (hasattr(st.session_state, 'show_changes_detail') and 
        st.session_state.show_changes_detail and st.session_state.changes_log):
        
        st.markdown("---")
        st.header("📊 Detailed Changes Log")
        
        changes_summary = get_changes_summary()
        if changes_summary:
            for tc_id, changes in changes_summary.items():
                with st.expander(f"Test Case {tc_id} ({len(changes)} changes)"):
                    for change in changes:
                        st.write(f"**{change['field']}:**")
                        st.write(f"  • From: `{change['old_value']}`")
                        st.write(f"  • To: `{change['new_value']}`")
                        st.write(f"  • When: {change['timestamp']}")
                        st.write("---")
        
        if st.button("Hide Changes Detail"):
            st.session_state.show_changes_detail = False
            st.rerun()

if __name__ == "__main__":
    main()
