import streamlit as st
from openai import OpenAI
import os
import tempfile
import json
import re
import streamlit.components.v1 as components

# Get API key from secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Set page config
st.set_page_config(
    page_title="Investment Thesis Formatter",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_data(ttl=3600)  # Cache for 1 hour to speed up repeated requests
def format_thesis_with_headers(text: str) -> str:
    """
    Use AI to reformat thesis text with proper section headers and colons
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""
        Please analyze this investment thesis and break it into 4-6 major sections with natural, flowing headers.
        
        Your job is to:
        1. Read through the text and identify the 4-6 MAJOR themes/topics (don't over-segment)
        2. Group related content together - combine smaller related points into substantial sections
        3. Create section headers that sound natural and professional - like how an investment analyst would organize major talking points
        4. Each section should have enough content to discuss for 30-60 seconds in a video presentation
        5. Headers should be concise but descriptive using investment language (e.g., "Activist Momentum", "Financial Position", "M&A Catalysts")
        6. Put each header on its own line followed by a colon, then a blank line
        7. Add blank lines between sections for clear separation
        8. Keep all original content but consolidate under fewer, more substantial headers
        
        Think like organizing major talking points for a 5-minute investment pitch - you want substantial sections, not tiny fragments.
        
        Original text:
        {text}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"Error formatting thesis: {str(e)}")
        return text

def extract_company_name(raw_text: str) -> str:
    """
    Simple function to extract company name from the very beginning of raw text
    """
    try:
        lines = raw_text.strip().split('\n')
        first_line = lines[0].strip()
        
        # Look for "CompanyName:" pattern
        if ':' in first_line:
            company_part = first_line.split(':')[0].strip()
            # Make sure it's not a section header
            section_headers = ['executive summary', 'background', 'thesis', 'analysis']
            if company_part.lower() not in section_headers and len(company_part) <= 15:
                return company_part.upper()
        
        # Look for all caps words in first line
        words = first_line.split()
        for word in words[:3]:  # Check first 3 words
            if word.isupper() and len(word) >= 2 and len(word) <= 8:
                excluded = ['THE', 'AND', 'FOR', 'INC', 'CORP', 'LLC']
                if word not in excluded:
                    return word
        
        return "INVESTMENT"
    except:
        return "INVESTMENT"

def parse_thesis_sections(formatted_text: str) -> list:
    """
    Parse the formatted thesis text into sections for visualization
    """
    sections = []
    lines = formatted_text.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if line.endswith(':') and line and not line.startswith(' '):
            # This is a section header
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content).strip()
                })
            current_section = line[:-1]  # Remove the colon
            current_content = []
        elif line:
            current_content.append(line)
    
    # Add the last section
    if current_section:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content).strip()
        })
    
    return sections

@st.cache_data(ttl=3600)  # Cache bullet points to speed up repeated requests
def create_bullet_points_batch(sections_data: list) -> list:
    """
    Create bullet points for all sections in a single API call for speed
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Prepare all sections for batch processing
        sections_text = ""
        for i, section in enumerate(sections_data):
            content = section['content'][:800]  # Limit content length
            sections_text += f"Section {i+1}: {section['title']}\nContent: {content}\n\n"
        
        prompt = f"""
        Analyze these investment thesis sections and create exactly 3 bullet points for each section.
        
        {sections_text}
        
        For each section, create 3 bullet points that are:
        - 5-8 words each
        - Key investment insights
        - Specific and actionable
        - Professional investment language
        
        Format your response as:
        Section 1:
        • First bullet point
        • Second bullet point  
        • Third bullet point
        
        Section 2:
        • First bullet point
        • Second bullet point
        • Third bullet point
        
        (Continue for all sections)
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=800,
            timeout=15
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the response into structured data
        processed_sections = []
        current_bullets = []
        
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith('Section'):
                if current_bullets:
                    processed_sections.append(current_bullets)
                current_bullets = []
            elif line.startswith('•') or line.startswith('-'):
                bullet = line.replace('•', '').replace('-', '').strip()
                if bullet:
                    current_bullets.append(bullet)
        
        # Add the last section
        if current_bullets:
            processed_sections.append(current_bullets)
        
        # Ensure we have the right number of sections with fallbacks
        final_sections = []
        for i, section in enumerate(sections_data):
            if i < len(processed_sections) and len(processed_sections[i]) >= 2:
                bullets = processed_sections[i][:3]  # Take first 3
                # Ensure exactly 3 bullets
                while len(bullets) < 3:
                    bullets.append(f"{section['title']} key insight")
                final_sections.append({
                    'title': section['title'],
                    'bullets': bullets
                })
            else:
                # Fallback bullets
                final_sections.append({
                    'title': section['title'],
                    'bullets': [
                        f"{section['title']} presents opportunity",
                        "Key metrics show potential", 
                        "Strategic value identified"
                    ]
                })
        
        return final_sections
        
    except Exception as e:
        print(f"Batch bullet generation failed: {str(e)}")
        # Fallback to simple bullets
        fallback_sections = []
        for section in sections_data:
            fallback_sections.append({
                'title': section['title'],
                'bullets': [
                    f"{section['title']} analysis complete",
                    "Investment opportunity identified",
                    "Strategic review in progress"
                ]
            })
        return fallback_sections

def display_brain_visualization(sections: list, company_name: str = "INVESTMENT"):
    """
    Display the brain visualization directly in Streamlit
    """
    # Process sections with optimized bullet generation
    with st.spinner("🧠 Generating investment insights..."):
        processed_sections = create_bullet_points_batch(sections)
    
    # Create the HTML content
    html_content = create_space_visualization_html(processed_sections, company_name)
    
    # Display directly in Streamlit with full height
    st.markdown("### 🧠 Interactive Investment Analysis")
    st.markdown("*Click on any section around the brain to explore key insights*")
    
    # Display the visualization
    components.html(html_content, height=800, scrolling=False)
    
    # Provide download option
    st.download_button(
        label="📥 Download Full-Screen Version",
        data=html_content,
        file_name=f"{company_name}_investment_analysis.html",
        mime="text/html",
        help="Download to open in full browser window"
    )

def create_space_visualization_html(sections: list, company_name: str = "INVESTMENT") -> str:
    """
    Create a professional brain-centered investment thesis visualization
    """
    # Convert sections to JSON safely
    sections_json = json.dumps(sections)
    
    # Create HTML template with optimized styling
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Thesis Analysis</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            font-family: 'Inter', sans-serif;
            cursor: default;
            height: 100vh;
            position: relative;
            overflow: hidden;
        }
        
        /* Animated background particles */
        .bg-particles {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(2px 2px at 20px 30px, rgba(79, 70, 229, 0.3), transparent),
                radial-gradient(2px 2px at 40px 70px, rgba(124, 58, 237, 0.2), transparent),
                radial-gradient(1px 1px at 90px 40px, rgba(236, 72, 153, 0.3), transparent);
            background-repeat: repeat;
            background-size: 200px 100px;
            animation: particleFloat 20s linear infinite;
            z-index: 1;
        }
        
        @keyframes particleFloat {
            0% { transform: translateY(0px) translateX(0px); }
            100% { transform: translateY(-100px) translateX(50px); }
        }
        
        #container {
            width: 100%;
            height: 100vh;
            position: relative;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* Main title */
        #main-title {
            position: absolute;
            top: 40px;
            left: 50%;
            transform: translateX(-50%);
            color: #ffffff;
            font-size: 32px;
            font-weight: 800;
            letter-spacing: 1px;
            text-align: center;
            background: linear-gradient(135deg, #ffffff, #e0e7ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(79, 70, 229, 0.3);
        }
        
        #subtitle {
            position: absolute;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            color: rgba(255, 255, 255, 0.7);
            font-size: 16px;
            font-weight: 400;
            letter-spacing: 0.5px;
            text-align: center;
        }
        
        /* Central brain container */
        #brain-container {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 0 auto;
        }
        
        #brain {
            width: 150px;
            height: 150px;
            background: linear-gradient(135deg, #4f46e5, #7c3aed, #ec4899);
            border-radius: 50%;
            position: relative;
            animation: brainPulse 3s ease-in-out infinite;
            box-shadow: 
                0 0 40px rgba(79, 70, 229, 0.4),
                inset 0 0 30px rgba(255, 255, 255, 0.1);
            cursor: default;
        }
        
        /* Brain neural network lines */
        #brain::before {
            content: '';
            position: absolute;
            top: 20%;
            left: 20%;
            width: 60%;
            height: 60%;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            animation: neuralPulse 2s ease-in-out infinite alternate;
        }
        
        #brain::after {
            content: '';
            position: absolute;
            top: 35%;
            left: 35%;
            width: 30%;
            height: 30%;
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 50%;
            animation: neuralPulse 2.5s ease-in-out infinite alternate-reverse;
        }
        
        @keyframes brainPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        @keyframes neuralPulse {
            0% { opacity: 0.3; transform: scale(1); }
            100% { opacity: 0.7; transform: scale(1.1); }
        }
        
        /* Brain icon inside */
        .brain-icon {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: rgba(255, 255, 255, 0.9);
            font-size: 36px;
            font-weight: 300;
        }
        
        /* Thesis sections positioned around brain */
        .thesis-section {
            position: absolute;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 16px 20px;
            min-width: 180px;
            max-width: 220px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        
        .thesis-section:hover {
            background: rgba(79, 70, 229, 0.2);
            border-color: rgba(79, 70, 229, 0.5);
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(79, 70, 229, 0.3);
        }
        
        .thesis-section h3 {
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 6px;
            text-align: center;
            letter-spacing: 0.3px;
        }
        
        .thesis-preview {
            color: rgba(255, 255, 255, 0.8);
            font-size: 11px;
            font-weight: 400;
            text-align: center;
            line-height: 1.4;
        }
        
        /* Connection lines from brain to sections */
        .connection-line {
            position: absolute;
            background: linear-gradient(90deg, transparent, rgba(79, 70, 229, 0.6), transparent);
            height: 2px;
            z-index: 5;
            animation: lineGlow 3s ease-in-out infinite;
        }
        
        @keyframes lineGlow {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 0.8; }
        }
        
        /* Content modal */
        #content-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        #content-modal.active {
            opacity: 1;
            visibility: visible;
        }
        
        .modal-content {
            background: linear-gradient(135deg, rgba(15, 15, 35, 0.95), rgba(26, 26, 46, 0.95));
            border: 1px solid rgba(79, 70, 229, 0.3);
            border-radius: 16px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            position: relative;
            backdrop-filter: blur(20px);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        }
        
        .modal-title {
            color: #ffffff;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 24px;
            text-align: center;
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .modal-bullets {
            list-style: none;
            padding: 0;
        }
        
        .modal-bullets li {
            color: #e0e7ff;
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 14px;
            padding-left: 25px;
            position: relative;
            line-height: 1.4;
        }
        
        .modal-bullets li::before {
            content: '→';
            position: absolute;
            left: 0;
            color: #4f46e5;
            font-weight: 700;
            font-size: 18px;
        }
        
        .close-btn {
            position: absolute;
            top: 12px;
            right: 16px;
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.7);
            font-size: 24px;
            cursor: pointer;
            transition: color 0.3s ease;
            line-height: 1;
        }
        
        .close-btn:hover {
            color: #ffffff;
        }
        
        /* Instructions */
        #instructions {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: rgba(255, 255, 255, 0.6);
            font-size: 12px;
            font-weight: 400;
            text-align: center;
            letter-spacing: 0.5px;
        }
    </style>
</head>
<body>
    <div class="bg-particles"></div>
    
    <div id="container">
        <div id="main-title">COMPANY_NAME_PLACEHOLDER ANALYSIS</div>
        <div id="subtitle">Investment Thesis Overview</div>
        
        <div id="brain-container">
            <div id="brain">
                <div class="brain-icon">🧠</div>
            </div>
        </div>
        
        <div id="instructions">
            Click on any section to view key insights
        </div>
    </div>
    
    <div id="content-modal">
        <div class="modal-content">
            <button class="close-btn">×</button>
            <div class="modal-title"></div>
            <ul class="modal-bullets"></ul>
        </div>
    </div>

    <script>
        const thesisSections = SECTIONS_JSON_PLACEHOLDER;
        
        // Position sections around the brain
        const positions = [
            { top: '15%', left: '20%', lineAngle: 135 },
            { top: '15%', right: '20%', lineAngle: 45 },
            { top: '45%', left: '12%', lineAngle: 180 },
            { top: '45%', right: '12%', lineAngle: 0 },
            { top: '70%', left: '20%', lineAngle: 225 },
            { top: '70%', right: '20%', lineAngle: 315 }
        ];
        
        function createThesisLayout() {
            const container = document.getElementById('container');
            
            thesisSections.forEach((section, index) => {
                if (index >= positions.length) return;
                
                // Create section element
                const sectionEl = document.createElement('div');
                sectionEl.className = 'thesis-section';
                sectionEl.style.position = 'absolute';
                
                // Apply position
                const pos = positions[index];
                Object.keys(pos).forEach(key => {
                    if (key !== 'lineAngle') {
                        sectionEl.style[key] = pos[key];
                    }
                });
                
                // Add content
                sectionEl.innerHTML = `
                    <h3>${section.title}</h3>
                    <div class="thesis-preview">Click to explore insights</div>
                `;
                
                // Add click handler
                sectionEl.addEventListener('click', () => {
                    showSectionDetails(section);
                });
                
                container.appendChild(sectionEl);
                
                // Create connection line
                createConnectionLine(index, pos);
            });
        }
        
        function createConnectionLine(index, position) {
            const line = document.createElement('div');
            line.className = 'connection-line';
            
            // Calculate line position and rotation
            const centerX = window.innerWidth / 2;
            const centerY = window.innerHeight / 2;
            
            let length = 120;
            let angle = position.lineAngle || 0;
            
            line.style.width = length + 'px';
            line.style.left = (centerX - length / 2) + 'px';
            line.style.top = centerY + 'px';
            line.style.transform = `rotate(${angle}deg)`;
            line.style.transformOrigin = 'center';
            
            document.getElementById('container').appendChild(line);
        }
        
        function showSectionDetails(section) {
            const modal = document.getElementById('content-modal');
            const title = modal.querySelector('.modal-title');
            const bullets = modal.querySelector('.modal-bullets');
            
            title.textContent = section.title;
            
            bullets.innerHTML = '';
            section.bullets.forEach(bullet => {
                const li = document.createElement('li');
                li.textContent = bullet;
                bullets.appendChild(li);
            });
            
            modal.classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('content-modal').classList.remove('active');
        }
        
        // Event listeners
        document.querySelector('.close-btn').addEventListener('click', closeModal);
        document.getElementById('content-modal').addEventListener('click', (e) => {
            if (e.target.id === 'content-modal') {
                closeModal();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
        
        // Initialize
        createThesisLayout();
    </script>
</body>
</html>'''
    
    # Replace placeholders safely
    html_content = html_template.replace('SECTIONS_JSON_PLACEHOLDER', sections_json)
    html_content = html_content.replace('COMPANY_NAME_PLACEHOLDER', company_name)
    
    return html_content

def main():
    # Comprehensive dark theme with proper styling
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Main app background */
        .stApp {
            background-color: #0a0a0a !important;
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        .main .block-container {
            background-color: #0a0a0a !important;
            padding-top: 3rem !important;
            padding-bottom: 3rem !important;
            max-width: 1200px !important;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em !important;
        }
        
        h1 {
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        h2 {
            font-size: 1.5rem !important;
            margin-bottom: 1rem !important;
            margin-top: 2rem !important;
        }
        
        /* All text elements */
        p, div, span, label, .stMarkdown {
            color: #e5e5e5 !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Text area styling */
        .stTextArea > div > div > textarea {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 2px solid #333333 !important;
            border-radius: 12px !important;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace !important;
            font-size: 14px !important;
            line-height: 1.6 !important;
            padding: 1rem !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #4f46e5 !important;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
            outline: none !important;
        }
        
        .stTextArea > div > div > textarea::placeholder {
            color: #888888 !important;
            font-style: italic !important;
        }
        
        /* Text area label */
        .stTextArea > label {
            color: #ffffff !important;
            font-weight: 500 !important;
            font-size: 1.1rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 1rem !important;
            padding: 0.75rem 2rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.2) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(79, 70, 229, 0.3) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0px) !important;
        }
        
        .stButton > button:disabled {
            background: #333333 !important;
            color: #666666 !important;
            transform: none !important;
            box-shadow: none !important;
            cursor: not-allowed !important;
        }
        
        /* Download button styling */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            padding: 0.5rem 1.5rem !important;
            margin-top: 0.5rem !important;
        }
        
        /* Messages */
        .stSuccess {
            background-color: #1a2e1a !important;
            color: #4ade80 !important;
            border: 1px solid #4ade80 !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            font-weight: 500 !important;
        }
        
        .stInfo {
            background-color: #1a1e2e !important;
            color: #60a5fa !important;
            border: 1px solid #60a5fa !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            font-weight: 500 !important;
        }
        
        .stError {
            background-color: #2e1a1a !important;
            color: #f87171 !important;
            border: 1px solid #f87171 !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            font-weight: 500 !important;
        }
        
        /* Columns */
        .stColumn {
            background-color: transparent !important;
        }
        
        /* Dividers */
        hr {
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, #333333, transparent) !important;
            margin: 2.5rem 0 !important;
        }
        
        /* Spinner */
        .stSpinner > div {
            border-color: #4f46e5 transparent #4f46e5 transparent !important;
        }
        
        /* Hide Streamlit elements */
        #MainMenu, footer, header, .stDeployButton {
            visibility: hidden !important;
            display: none !important;
        }
        
        /* Custom animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .main .block-container > div {
            animation: fadeIn 0.5s ease-out !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📊 Investment Thesis Formatter")
    st.markdown("Transform your thesis into organized sections with clear headers")
    st.markdown("---")
    
    # Text input
    st.header("📝 Paste Your Investment Thesis")
    
    # Use session state to track the current text
    if 'current_text' not in st.session_state:
        st.session_state.current_text = ""
    if 'just_formatted' not in st.session_state:
        st.session_state.just_formatted = False
    
    thesis_text = st.text_area(
        "Thesis Text:",
        value=st.session_state.current_text,
        height=400,
        placeholder="Paste your investment thesis here...",
        key="thesis_input"
    )
    
    # Update session state when user types
    if thesis_text != st.session_state.current_text:
        st.session_state.current_text = thesis_text
    
    # Format button
    col1, col2 = st.columns([1, 1])
    
    with col1:
        format_button = st.button("🔄 Format with Headers", type="primary", disabled=not thesis_text)
    
    with col2:
        # View visualization button - NOW MUCH FASTER!
        has_formatted_text = st.session_state.current_text and ":" in st.session_state.current_text
        viz_button = st.button("🧠 Launch Brain Visualization", type="secondary", disabled=not has_formatted_text)
    
    # Process formatting
    if format_button:
        if thesis_text:
            # FIRST: Extract and store company name from original text
            company_name = extract_company_name(thesis_text)
            st.session_state.company_name = company_name
            
            # Clear any existing messages and show loading
            st.empty()
            with st.spinner("🤖 AI is analyzing your thesis and creating sections... (This may take 10-15 seconds)"):
                formatted_text = format_thesis_with_headers(thesis_text)
                
                # Update results
                if formatted_text and formatted_text != thesis_text:
                    st.session_state.current_text = formatted_text
                    st.session_state.just_formatted = True
                    st.success("✅ **Thesis formatted successfully!** The text above has been updated with section headers.")
                    st.rerun()
                else:
                    st.error("❌ **Failed to format thesis.** Please check your API key and try again.")
        else:
            st.error("Please provide thesis text.")
    
    # Process visualization
    if viz_button:
        # Use stored company name if available, otherwise extract from current text
        if hasattr(st.session_state, 'company_name'):
            stored_company = st.session_state.company_name
        else:
            stored_company = extract_company_name(st.session_state.current_text)
        
        # Parse the thesis sections for the visualization
        sections = parse_thesis_sections(st.session_state.current_text)
        
        # Display the visualization directly in the app
        display_brain_visualization(sections, stored_company)
    
    # Show tip only if text has been formatted AND we didn't just format it
    if (st.session_state.current_text and ":" in st.session_state.current_text and 
        not st.session_state.just_formatted):
        st.info("💡 **Tip:** Your thesis has been formatted with clear section headers. You can now launch the brain visualization!")
    
    # Reset the just_formatted flag after showing success
    if st.session_state.just_formatted:
        st.session_state.just_formatted = False

if __name__ == "__main__":
    main()
