import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_review_analyzer import PlayStoreReviewAnalyzer

# Set page config
st.set_page_config(
    page_title="Play Store Review Analyzer",
    page_icon="📱",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .reportview-container {
        background: #f0f2f6;
    }
    .review-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .history-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 0.25rem;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .history-item:hover {
        background-color: rgba(0,0,0,0.05);
    }
    .history-date {
        font-size: 0.8rem;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

def load_report(app_id: str) -> dict:
    """Load the analysis report from JSON file."""
    report_path = f"reports/{app_id}_report.json"
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            return json.load(f)
    return None

def get_analysis_history():
    """Get list of previously analyzed apps."""
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        return []
    
    history = []
    for file in os.listdir(reports_dir):
        if file.endswith('_report.json'):
            with open(os.path.join(reports_dir, file), 'r') as f:
                report = json.load(f)
                history.append({
                    'app_id': file.replace('_report.json', ''),
                    'app_name': report['app_info']['title'],
                    'date': report['generated_at']
                })
    return sorted(history, key=lambda x: x['date'], reverse=True)

def save_history(history):
    """Save analysis history to a JSON file."""
    history_file = "reports/analysis_history.json"
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

def create_rating_distribution_plot(reviews_df: pd.DataFrame) -> go.Figure:
    """Create a rating distribution plot using Plotly."""
    fig = px.histogram(
        reviews_df,
        x='score',
        title='Rating Distribution',
        nbins=5,
        labels={'score': 'Rating', 'count': 'Number of Reviews'}
    )
    fig.update_layout(
        xaxis_title="Rating",
        yaxis_title="Number of Reviews",
        showlegend=False
    )
    return fig

def create_sentiment_distribution_plot(sentiment_data: dict) -> go.Figure:
    """Create a sentiment distribution plot using Plotly."""
    fig = px.pie(
        values=list(sentiment_data.values()),
        names=list(sentiment_data.keys()),
        title='Sentiment Distribution'
    )
    return fig

def create_topics_plot(topics_data: dict, title: str) -> go.Figure:
    """Create a horizontal bar plot for topics/issues/praises."""
    df = pd.DataFrame({
        'Item': list(topics_data.keys()),
        'Count': list(topics_data.values())
    }).sort_values('Count', ascending=True)
    
    fig = px.bar(
        df,
        x='Count',
        y='Item',
        title=title,
        orientation='h'
    )
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(df) * 25)
    )
    return fig

def display_review_card(review: dict, sentiment: str):
    """Display a review in a card format."""
    st.markdown(f"""
        <div class="review-card">
            <div style="color: {'#2ecc71' if sentiment == 'positive' else '#e74c3c' if sentiment == 'negative' else '#7f8c8d'}">
                Rating: {review['score']} ⭐
            </div>
            <div style="margin-top: 0.5rem;">
                {review['content']}
            </div>
        </div>
    """, unsafe_allow_html=True)

def get_country_flag(country_code: str) -> str:
    """Convert country code to flag emoji."""
    # Convert country code to uppercase
    code = country_code.upper()
    # Convert country code to regional indicator symbols
    flag = ''.join([chr(ord(c) + 127397) for c in code])
    return flag

def get_country_options():
    """Get list of country options with flags."""
    countries = [
        "us", "gb", "ca", "au", "jp", "in", "de", "fr", "br", "ru",
        "es", "it", "kr", "cn", "mx", "sg", "ae", "sa", "za", "nl",
        "se", "ch", "no", "dk", "fi", "ie", "be", "at", "pl", "cz",
        "hu", "gr", "il", "ro", "sk", "ua", "cl", "ar", "co", "pe",
        "ve", "my", "ph", "id", "th", "vn", "tr", "eg", "pk", "bd",
        "lk", "np", "kh", "la", "mm", "bn", "kz", "uz", "az", "ge",
        "am", "kg", "tj", "tm", "af", "iq", "sy", "lb", "jo", "kw",
        "bh", "om", "qa", "ye", "et", "ke", "ng", "gh", "ma", "dz",
        "tn", "ly", "sd", "sn", "ci", "cm", "ug", "zm", "zw", "mw",
        "ao", "mz", "na", "bw", "ls", "sz", "km", "mg", "mu", "sc",
        "cv", "gm", "gw", "lr", "sl", "st", "ne", "bf", "ml", "mr",
        "td", "cf", "gq", "cg", "cd", "bi", "rw", "dj", "er", "so",
        "ss", "tz"
    ]
    return {f"{get_country_flag(code)} {code.upper()}": code for code in countries}

def clear_history():
    """Clear all analysis history by removing report files."""
    reports_dir = "reports"
    if os.path.exists(reports_dir):
        for file in os.listdir(reports_dir):
            if file.endswith('_report.json'):
                os.remove(os.path.join(reports_dir, file))
        st.success("History cleared successfully!")

def display_analysis_results(report):
    """Display analysis results in a consistent format."""
    # App Info
    st.header("App Information")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("App Name", report['app_info']['title'])
    with col2:
        st.metric("Developer", report['app_info']['developer'])
    with col3:
        st.metric("Rating", f"{report['app_info']['score']:.1f}")
    with col4:
        st.metric("Total Reviews", report['app_info']['reviews'])
    
    # Analysis Results
    st.header("Analysis Results")
    
    # Rating and Sentiment Distribution
    col1, col2 = st.columns(2)
    with col1:
        # Create rating distribution data from the report
        rating_dist = report['analysis']['rating_distribution']
        rating_df = pd.DataFrame({
            'Rating': list(rating_dist.keys()),
            'Count': list(rating_dist.values())
        })
        fig1 = px.bar(
            rating_df,
            x='Rating',
            y='Count',
            title='Rating Distribution',
            labels={'Rating': 'Rating', 'Count': 'Number of Reviews'}
        )
        fig1.update_layout(
            xaxis_title="Rating",
            yaxis_title="Number of Reviews",
            showlegend=False
        )
        st.plotly_chart(fig1, use_container_width=True, key="rating_distribution")
    
    with col2:
        fig2 = create_sentiment_distribution_plot(report['analysis']['sentiment_distribution'])
        st.plotly_chart(fig2, use_container_width=True, key="sentiment_distribution")
    
    # Topics, Issues, and Praises
    st.subheader("Key Insights")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fig3 = create_topics_plot(
            report['analysis']['common_topics'],
            "Common Topics"
        )
        st.plotly_chart(fig3, use_container_width=True, key="common_topics")
    
    with col2:
        fig4 = create_topics_plot(
            report['analysis']['common_issues'],
            "Common Issues"
        )
        st.plotly_chart(fig4, use_container_width=True, key="common_issues")
    
    with col3:
        fig5 = create_topics_plot(
            report['analysis']['common_praises'],
            "Common Praises"
        )
        st.plotly_chart(fig5, use_container_width=True, key="common_praises")
    
    # Raw Data
    if st.checkbox("Show Raw Data"):
        st.subheader("Raw Analysis Data")
        st.json(report['analysis'])

def main():
    # Sidebar
    st.sidebar.title("📱 Play Store Review Analyzer")
    st.sidebar.markdown("Analyze and visualize app reviews from the Google Play Store")
    
    # App ID input
    app_id = st.sidebar.text_input(
        "App ID",
        value=st.session_state.get('app_id', "com.nianticlabs.pokemongo"),
        help="Enter the Google Play Store app ID (e.g., com.nianticlabs.pokemongo)"
    )
    
    # Analysis Type Selection
    analysis_type = st.sidebar.radio(
        "Analysis Type",
        ["All Reviews", "Negative Reviews Only"],
        help="Choose whether to analyze all reviews or only negative reviews (1-3 stars)"
    )
    
    # Number of reviews
    if analysis_type == "All Reviews":
        review_count = st.sidebar.slider(
            "Number of Reviews",
            min_value=5,
            max_value=1000,
            value=100,
            step=5
        )
    else:
        review_count = st.sidebar.select_slider(
            "Number of Reviews",
            options=[10, 100, 1000],
            value=100,
            help="Select the number of negative reviews to analyze"
        )
    
    # Language and country selection
    col1, col2 = st.sidebar.columns(2)
    with col1:
        lang = st.selectbox("Language", [
            "en", "es", "fr", "de", "ja", "ko", "ru", "zh", "hi", "ar",
            "pt", "it", "nl", "pl", "tr", "vi", "th", "id", "ms", "fil",
            "uk", "cs", "el", "he", "ro", "hu", "da", "sv", "fi", "no",
            "sk", "hr", "ca", "bg", "sr", "et", "lv", "lt", "sl", "is",
            "fa", "bn", "ur", "sw", "am", "ne", "si", "km", "my", "ka",
            "hy", "az", "eu", "be", "bs", "cy", "gl", "ka", "lb", "mk",
            "ml", "mr", "mn", "mt", "nb", "or", "ps", "pa", "qu", "rm",
            "rw", "sa", "sd", "sn", "so", "sq", "sr", "st", "su", "sw",
            "ta", "te", "tg", "ti", "tk", "tl", "tn", "to", "ts", "tt",
            "ug", "uk", "ur", "uz", "ve", "vi", "vo", "wa", "wo", "xh",
            "yi", "yo", "zu"
        ])
    with col2:
        country_options = get_country_options()
        selected_country = st.selectbox(
            "Country",
            options=list(country_options.keys()),
            format_func=lambda x: x,
            help="Select a country"
        )
        country = country_options[selected_country]
    
    # Add Analyze Reviews button to sidebar
    if st.sidebar.button("🔍 Analyze Reviews", type="primary"):
        try:
            with st.spinner("Analyzing reviews..."):
                analyzer = PlayStoreReviewAnalyzer(app_id, lang, country)
                
                # Fetch app info
                analyzer.fetch_app_info()
                
                # Fetch reviews based on analysis type
                if analysis_type == "Negative Reviews Only":
                    analyzer.fetch_reviews(count=review_count * 2)  # Fetch more to ensure enough negative reviews
                    analyzer.reviews = [r for r in analyzer.reviews if r.get('score', 0) <= 3]
                else:
                    analyzer.fetch_reviews(count=review_count)
                
                # Generate report
                report_path = analyzer.generate_report()
                st.success(f"Analysis complete! Report saved to {report_path}")
                
                # Save to history
                history = get_analysis_history()
                history.append({
                    'app_id': app_id,
                    'app_name': analyzer.app_info['title'],
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'report_path': report_path
                })
                save_history(history)
                
                # Reload the page to show the new report
                st.rerun()
                
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            st.info("Please check if the app ID is correct and try again.")
    
    # Load and display report
    report = load_report(app_id)
    if report:
        display_analysis_results(report)
    else:
        st.info("No report found. Please analyze an app first.")
    
    # Analysis History (moved to bottom of sidebar)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Recent Analyses")
    
    # Add clear history button
    if st.sidebar.button("🗑️ Clear History", type="secondary"):
        clear_history()
        st.rerun()
    
    history = get_analysis_history()
    if history:
        for item in history:
            # Create a clickable history item
            if st.sidebar.button(
                f"{item['app_name']}\n{item['date'][:10]}",
                key=f"history-{item['app_id']}",
                help="Click to load this analysis"
            ):
                st.session_state.app_id = item['app_id']
                st.rerun()
    else:
        st.sidebar.info("No previous analysis found")

if __name__ == "__main__":
    main() 