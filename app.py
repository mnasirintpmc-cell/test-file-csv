import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# Configure the page
st.set_page_config(
    page_title="Main Seal Test Sequence Viewer",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .phase-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .highlight {
        background-color: #fff3cd;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_csv_data():
    try:
        # Read the CSV file
        df = pd.read_csv('MainSealSet2.csv', delimiter=';')
        
        # Create readable column names mapping
        column_mapping = {
            'TST_SpeedDem': 'Speed_RPM',
            'TST_CellPresDemand': 'Cell_Pressure_bar',
            'TST_InterPresDemand': 'Interface_Pressure_bar',
            'TST_InterBPDemand_DE': 'BP_Drive_End_bar',
            'TST_InterBPDemand_NDE': 'BP_Non_Drive_End_bar',
            'TST_GasInjectionDemand': 'Gas_Injection_bar',
            'TST_StepDuration': 'Duration_s',
            'TST_APFlag': 'Auto_Proceed',
            'TST_TempDemand': 'Temperature_C',
            'TST_GasType': 'Gas_Type',
            'TST_TestMode': 'Test_Mode',
            'TST_MeasurementReq': 'Measurement',
            'TST_TorqueCheck': 'Torque_Check'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Convert boolean-like columns to more readable values
        df['Auto_Proceed'] = df['Auto_Proceed'].map({0: 'No', 1: 'Yes'})
        df['Measurement'] = df['Measurement'].map({0: 'No', 1: 'Yes'})
        df['Torque_Check'] = df['Torque_Check'].map({0: 'No'})
        df['Test_Mode'] = df['Test_Mode'].map({1: 'Mode 1', 2: 'Mode 2'})
        
        # Add step numbers
        df.insert(0, 'Step', range(1, len(df) + 1))
        
        return df
    
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

def create_test_progress_chart(df):
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Pressure Parameters Over Time', 'Temperature and Speed Over Time'),
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4]
    )
    
    # Pressure parameters
    fig.add_trace(
        go.Scatter(x=df['Step'], y=df['Cell_Pressure_bar'], 
                  name='Cell Pressure', line=dict(color='blue')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['Step'], y=df['Interface_Pressure_bar'], 
                  name='Interface Pressure', line=dict(color='red')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['Step'], y=df['BP_Drive_End_bar'], 
                  name='BP Drive End', line=dict(color='green')),
        row=1, col=1
    )
    
    # Temperature and Speed
    fig.add_trace(
        go.Scatter(x=df['Step'], y=df['Temperature_C'], 
                  name='Temperature', line=dict(color='orange'), yaxis='y2'),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['Step'], y=df['Speed_RPM'], 
                  name='Speed', line=dict(color='purple'), yaxis='y3'),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="Test Step", row=2, col=1)
    fig.update_yaxes(title_text="Pressure (bar)", row=1, col=1)
    fig.update_yaxes(title_text="Temperature (°C)", row=2, col=1)
    fig.update_yaxes(title_text="Speed (RPM)", row=2, col=1, overlaying='y2', side='right')
    
    fig.update_layout(height=600, showlegend=True, title_text="Test Sequence Overview")
    return fig

def create_phase_analysis(df):
    # Simple phase detection based on major parameter changes
    phases = []
    current_phase = {'start': 1, 'steps': [df.iloc[0]]}
    
    for i in range(1, len(df)):
        current_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # Check for significant changes
        temp_change = abs(current_row['Temperature_C'] - prev_row['Temperature_C']) > 50
        speed_change = current_row['Speed_RPM'] != prev_row['Speed_RPM']
        mode_change = current_row['Test_Mode'] != prev_row['Test_Mode']
        
        if temp_change or speed_change or mode_change:
            phases.append(current_phase)
            current_phase = {'start': i+1, 'steps': [current_row]}
        else:
            current_phase['steps'].append(current_row)
    
    phases.append(current_phase)
    return phases

def main():
    # Header
    st.markdown('<h1 class="main-header">⚙️ Main Seal Test Sequence Viewer</h1>', 
                unsafe_allow_html=True)
    
    # Load data
    df = load_csv_data()
    
    if df is None:
        st.error("Could not load CSV data. Please ensure 'MainSealSet2.csv' is in the correct location.")
        return
    
    # Sidebar
    st.sidebar.title("Navigation")
    view_option = st.sidebar.radio(
        "Select View:",
        ["📊 Dashboard Overview", "📋 Full Data Table", "🔍 Phase Analysis", "📈 Charts & Graphs"]
    )
    
    # Main content based on selection
    if view_option == "📊 Dashboard Overview":
        show_dashboard(df)
    elif view_option == "📋 Full Data Table":
        show_data_table(df)
    elif view_option == "🔍 Phase Analysis":
        show_phase_analysis(df)
    elif view_option == "📈 Charts & Graphs":
        show_charts(df)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Tip**: Use the different views to analyze the test sequence from various perspectives.")

def show_dashboard(df):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Test Steps", len(df))
    with col2:
        st.metric("Temperature Range", f"{df['Temperature_C'].min()}°C - {df['Temperature_C'].max()}°C")
    with col3:
        st.metric("Max Cell Pressure", f"{df['Cell_Pressure_bar'].max()} bar")
    with col4:
        st.metric("Test Modes", len(df['Test_Mode'].unique()))
    
    # Quick statistics
    st.subheader("Quick Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Pressure Statistics**")
        pressure_stats = df[['Cell_Pressure_bar', 'Interface_Pressure_bar', 
                           'BP_Drive_End_bar', 'BP_Non_Drive_End_bar']].describe()
        st.dataframe(pressure_stats, use_container_width=True)
    
    with col2:
        st.write("**Test Configuration**")
        config_data = {
            'Parameter': ['Gas Type', 'Auto Proceed Steps', 'Measurement Steps', 'Total Duration'],
            'Value': [
                df['Gas_Type'].iloc[0],
                len(df[df['Auto_Proceed'] == 'Yes']),
                len(df[df['Measurement'] == 'Yes']),
                f"{df['Duration_s'].sum()} seconds"
            ]
        }
        st.dataframe(pd.DataFrame(config_data), use_container_width=True)
    
    # Interactive chart
    st.subheader("Test Sequence Progress")
    fig = create_test_progress_chart(df)
    st.plotly_chart(fig, use_container_width=True)

def show_data_table(df):
    st.subheader("Complete Test Sequence Data")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        temp_filter = st.multiselect(
            "Filter by Temperature:",
            options=sorted(df['Temperature_C'].unique()),
            default=sorted(df['Temperature_C'].unique())
        )
    
    with col2:
        mode_filter = st.multiselect(
            "Filter by Test Mode:",
            options=df['Test_Mode'].unique().tolist(),
            default=df['Test_Mode'].unique().tolist()
        )
    
    with col3:
        auto_proceed_filter = st.multiselect(
            "Filter by Auto Proceed:",
            options=df['Auto_Proceed'].unique().tolist(),
            default=df['Auto_Proceed'].unique().tolist()
        )
    
    # Apply filters
    filtered_df = df[
        (df['Temperature_C'].isin(temp_filter)) &
        (df['Test_Mode'].isin(mode_filter)) &
        (df['Auto_Proceed'].isin(auto_proceed_filter))
    ]
    
    st.info(f"Showing {len(filtered_df)} of {len(df)} steps")
    
    # Display data with formatting
    styled_df = filtered_df.style.apply(
        lambda x: ['background-color: #fff3cd' if x.name in ['Speed_RPM', 'Cell_Pressure_bar'] 
                  and x.iloc[0] > 0 else '' for _ in x], 
        axis=1
    )
    
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_test_sequence.csv",
        mime="text/csv"
    )

def show_phase_analysis(df):
    st.subheader("Test Phase Analysis")
    
    phases = create_phase_analysis(df)
    
    for i, phase in enumerate(phases):
        phase_df = pd.DataFrame(phase['steps'])
        
        with st.expander(f"Phase {i+1} (Steps {phase['start']}-{phase['start'] + len(phase_df) - 1})", expanded=i==0):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Steps", len(phase_df))
            with col2:
                st.metric("Temperature", f"{phase_df['Temperature_C'].iloc[0]}°C")
            with col3:
                st.metric("Test Mode", phase_df['Test_Mode'].iloc[0])
            with col4:
                st.metric("Duration", f"{phase_df['Duration_s'].sum()}s")
            
            # Phase summary
            st.write("**Phase Parameters:**")
            summary_data = {
                'Parameter': ['Speed (RPM)', 'Cell Pressure (bar)', 'Interface Pressure (bar)', 
                            'BP Drive End (bar)', 'BP Non-Drive End (bar)', 'Gas Injection (bar)'],
                'Min': [
                    phase_df['Speed_RPM'].min(),
                    phase_df['Cell_Pressure_bar'].min(),
                    phase_df['Interface_Pressure_bar'].min(),
                    phase_df['BP_Drive_End_bar'].min(),
                    phase_df['BP_Non_Drive_End_bar'].min(),
                    phase_df['Gas_Injection_bar'].min()
                ],
                'Max': [
                    phase_df['Speed_RPM'].max(),
                    phase_df['Cell_Pressure_bar'].max(),
                    phase_df['Interface_Pressure_bar'].max(),
                    phase_df['BP_Drive_End_bar'].max(),
                    phase_df['BP_Non_Drive_End_bar'].max(),
                    phase_df['Gas_Injection_bar'].max()
                ],
                'Avg': [
                    phase_df['Speed_RPM'].mean(),
                    phase_df['Cell_Pressure_bar'].mean(),
                    phase_df['Interface_Pressure_bar'].mean(),
                    phase_df['BP_Drive_End_bar'].mean(),
                    phase_df['BP_Non_Drive_End_bar'].mean(),
                    phase_df['Gas_Injection_bar'].mean()
                ]
            }
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
            
            # Show phase data
            if st.checkbox(f"Show detailed steps for Phase {i+1}", key=f"show_phase_{i}"):
                st.dataframe(phase_df, use_container_width=True)

def show_charts(df):
    st.subheader("Interactive Charts and Analysis")
    
    chart_type = st.selectbox(
        "Select Chart Type:",
        ["Pressure vs Temperature", "Parameter Distribution", "Time Series Analysis", "Correlation Heatmap"]
    )
    
    if chart_type == "Pressure vs Temperature":
        fig = px.scatter(df, x='Temperature_C', y='Cell_Pressure_bar', 
                        color='Test_Mode', size='Duration_s',
                        hover_data=['Step', 'Speed_RPM'],
                        title="Cell Pressure vs Temperature by Test Mode")
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "Parameter Distribution":
        param = st.selectbox("Select Parameter:", 
                           ['Cell_Pressure_bar', 'Interface_Pressure_bar', 
                            'BP_Drive_End_bar', 'Speed_RPM', 'Temperature_C'])
        
        fig = px.histogram(df, x=param, color='Test_Mode', 
                          title=f"Distribution of {param.replace('_', ' ')}")
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "Time Series Analysis":
        params = st.multiselect("Select parameters to plot:", 
                              ['Cell_Pressure_bar', 'Interface_Pressure_bar', 
                               'BP_Drive_End_bar', 'Speed_RPM', 'Temperature_C'],
                              default=['Cell_Pressure_bar', 'Temperature_C'])
        
        if params:
            fig = go.Figure()
            for param in params:
                fig.add_trace(go.Scatter(x=df['Step'], y=df[param], 
                                       name=param.replace('_', ' ')))
            fig.update_layout(title="Parameter Trends Over Test Steps",
                            xaxis_title="Test Step",
                            yaxis_title="Value")
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Correlation Heatmap":
        numeric_cols = df.select_dtypes(include=['number']).columns
        corr_matrix = df[numeric_cols].corr()
        
        fig = px.imshow(corr_matrix, 
                       title="Correlation Matrix of Numerical Parameters",
                       color_continuous_scale='RdBu_r',
                       aspect="auto")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
