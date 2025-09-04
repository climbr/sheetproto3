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
        background: linear-gradient(45deg, #17a2b8, #138496);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'changes' not in st.session_state:
        st.session_state.changes = {}
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None

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
    
    # Reorder columns to match expected schema
    df = df[expected_columns]
    
    return df

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
    if old_value != new_value:
        change_key = f"{test_case_id}_{field}"
        st.session_state.changes[change_key] = {
            'test_case_id': test_case_id,
            'field': field,
            'old_value': old_value,
            'new_value': new_value,
            'timestamp': datetime.now().isoformat()
        }

def get_changes_summary():
    """Get summary of all changes made"""
    if not st.session_state.changes:
        return None
    
    changes_by_test = {}
    for change in st.session_state.changes.values():
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
                    st.session_state.current_index = 0
                    st.session_state.changes = {}
                
                st.success(f"✅ Loaded {len(df)} test cases")
                
            except Exception as e:
                st.error(f"Error loading CSV: {str(e)}")
                return
        
        # Navigation controls
        if st.session_state.df is not None:
            st.header("🧭 Navigation")
            
            total_cases = len(st.session_state.df)
            current_case_num = st.session_state.current_index + 1
            
            st.write(f"**Test Case {current_case_num} of {total_cases}**")
            
            # Progress bar
            progress = st.session_state.current_index / max(1, total_cases - 1)
            st.progress(progress)
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Previous", disabled=st.session_state.current_index == 0):
                    st.session_state.current_index = max(0, st.session_state.current_index - 1)
                    st.rerun()
            
            with col2:
                if st.button("Next ➡️", disabled=st.session_state.current_index >= total_cases - 1):
                    st.session_state.current_index = min(total_cases - 1, st.session_state.current_index + 1)
                    st.rerun()
            
            # Jump to specific test case
            st.write("**Jump to Test Case:**")
            jump_to = st.selectbox(
                "Select test case:",
                options=range(total_cases),
                index=st.session_state.current_index,
                format_func=lambda x: f"Test Case {x + 1} - {st.session_state.df.iloc[x]['Test Case'][:30]}..." 
                if len(str(st.session_state.df.iloc[x]['Test Case'])) > 30 
                else f"Test Case {x + 1} - {st.session_state.df.iloc[x]['Test Case']}",
                key="jump_select"
            )
            
            if jump_to != st.session_state.current_index:
                st.session_state.current_index = jump_to
                st.rerun()
            
            # Filter options
            st.header("🔍 Filters")
            categories = ['All'] + sorted(st.session_state.df['Category'].dropna().unique().tolist())
            selected_category = st.selectbox("Filter by Category:", categories)
            
            statuses = ['All'] + sorted(st.session_state.df['Test Status'].dropna().unique().tolist())
            selected_status = st.selectbox("Filter by Status:", statuses)
            
            # Export section
            st.header("💾 Export")
            changes_summary = get_changes_summary()
            if changes_summary:
                st.write(f"**{len(st.session_state.changes)} changes made**")
                if st.button("📊 Show Changes Summary"):
                    st.session_state.show_changes = True
            
            csv_data = export_data()
            if csv_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="⬇️ Download Updated CSV",
                    data=csv_data,
                    file_name=f"test_cases_updated_{timestamp}.csv",
                    mime="text/csv",
                    help="Download your updated test cases with all changes"
                )
    
    # Main content area
    if st.session_state.df is not None and len(st.session_state.df) > 0:
        current_test = st.session_state.df.iloc[st.session_state.current_index].copy()
        test_id = current_test.get('ID', st.session_state.current_index)
        
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
            if st.session_state.current_index < len(st.session_state.df) - 1:
                if st.button("Save & Next ➡️", type="primary"):
                    st.session_state.current_index += 1
                    st.rerun()
        
        # Test case form
        with st.form(key=f"test_case_form_{st.session_state.current_index}"):
            
            # Basic Information
            st.subheader("📋 Basic Information")
            col1, col2 = st.columns(2)
            
            with col1:
                new_category = st.text_input(
                    "Category", 
                    value=str(current_test.get('Category', '')),
                    key=f"category_{st.session_state.current_index}"
                )
            
            with col2:
                new_test_case = st.text_input(
                    "Test Case Name", 
                    value=str(current_test.get('Test Case', '')),
                    key=f"test_case_{st.session_state.current_index}"
                )
            
            # Test Details
            st.subheader("🔍 Test Details")
            new_description = st.text_area(
                "Test Description", 
                value=str(current_test.get('Test Description', '')),
                height=100,
                key=f"description_{st.session_state.current_index}"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                new_test_input = st.text_area(
                    "Test Input", 
                    value=str(current_test.get('Test Input', '')),
                    height=80,
                    key=f"input_{st.session_state.current_index}"
                )
            
            with col2:
                new_expected = st.text_area(
                    "Expected Outcome", 
                    value=str(current_test.get('Expected Outcome', '')),
                    height=80,
                    key=f"expected_{st.session_state.current_index}"
                )
            
            # Test Environment
            st.subheader("🌐 Test Environment")
            new_env = st.text_input(
                "Test Environment", 
                value=str(current_test.get('Test Env', '')),
                key=f"env_{st.session_state.current_index}"
            )
            
            # Test Results
            st.subheader("✅ Test Results")
            col1, col2 = st.columns(2)
            
            with col1:
                new_status = st.selectbox(
                    "Test Status",
                    options=['Pending', 'Passed', 'Failed', 'Blocked'],
                    index=['Pending', 'Passed', 'Failed', 'Blocked'].index(
                        current_test.get('Test Status', 'Pending') 
                        if current_test.get('Test Status', 'Pending') in ['Pending', 'Passed', 'Failed', 'Blocked']
                        else 'Pending'
                    ),
                    key=f"status_{st.session_state.current_index}"
                )
            
            with col2:
                current_date = current_test.get('Date of Last Test', '')
                if current_date and current_date != '':
                    try:
                        current_date = pd.to_datetime(current_date).date()
                    except:
                        current_date = date.today()
                else:
                    current_date = None
                
                new_date = st.date_input(
                    "Date of Last Test", 
                    value=current_date,
                    key=f"date_{st.session_state.current_index}"
                )
            
            new_observed = st.text_area(
                "Observed Outcome", 
                value=str(current_test.get('Observed Outcome', '')),
                height=100,
                key=f"observed_{st.session_state.current_index}"
            )
            
            # Notes
            st.subheader("📝 Notes")
            new_notes = st.text_area(
                "Notes", 
                value=str(current_test.get('Notes', '')),
                height=80,
                key=f"notes_{st.session_state.current_index}"
            )
            
            # Form submission
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
            
            if submitted:
                # Track all changes
                track_change('Category', current_test.get('Category', ''), new_category, test_id)
                track_change('Test Case', current_test.get('Test Case', ''), new_test_case, test_id)
                track_change('Test Description', current_test.get('Test Description', ''), new_description, test_id)
                track_change('Test Input', current_test.get('Test Input', ''), new_test_input, test_id)
                track_change('Expected Outcome', current_test.get('Expected Outcome', ''), new_expected, test_id)
                track_change('Test Env', current_test.get('Test Env', ''), new_env, test_id)
                track_change('Test Status', current_test.get('Test Status', ''), new_status, test_id)
                track_change('Date of Last Test', current_test.get('Date of Last Test', ''), str(new_date), test_id)
                track_change('Observed Outcome', current_test.get('Observed Outcome', ''), new_observed, test_id)
                track_change('Notes', current_test.get('Notes', ''), new_notes, test_id)
                
                # Update the dataframe
                st.session_state.df.iloc[st.session_state.current_index] = [
                    test_id, new_category, new_test_case, new_description, new_test_input,
                    new_expected, new_env, new_observed, new_status, str(new_date), new_notes
                ]
                
                st.success("✅ Changes saved successfully!")
                st.rerun()
        
        # Show changes summary if requested
        if hasattr(st.session_state, 'show_changes') and st.session_state.show_changes:
            changes_summary = get_changes_summary()
            if changes_summary:
                st.markdown("""
                <div class="changes-summary">
                    <h3>📊 Changes Summary</h3>
                </div>
                """, unsafe_allow_html=True)
                
                for tc_id, changes in changes_summary.items():
                    st.write(f"**Test Case {tc_id}:** {len(changes)} changes")
                    for change in changes:
                        st.write(f"  • {change['field']}: '{change['old_value']}' → '{change['new_value']}'")
            
            if st.button("Hide Changes"):
                st.session_state.show_changes = False
                st.rerun()
    
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

if __name__ == "__main__":
    main()

from transformers import pipeline

@st.cache_resource
def load_llm():
    return pipeline("text-generation", model="microsoft/DialoGPT-medium")

def improve_test_description(original_desc, business_rules):
    generator = load_llm()
    prompt = f"""
    Business Rules: {business_rules}
    
    Original Test Description: {original_desc}
    
    Improved Test Description:"""
    
    result = generator(prompt, max_length=200, num_return_sequences=1)
    return result[0]['generated_text']
