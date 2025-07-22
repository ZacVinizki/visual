import streamlit as st
from openai import OpenAI
import os
import tempfile
import webbrowser
import json
import re
import streamlit.components.v1 as components
import base64

# Get API key from secrets (your working setup)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Set page config
st.set_page_config(
    page_title="Investment Thesis Formatter",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def format_thesis_with_headers(text: str) -> str:
    """
    Use AI to reformat thesis text with proper section headers and colons
    """
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
    
    CRITICAL: Headers must be proper nouns/phrases, NOT sentences. Do NOT start headers with words like "And", "But", "The", etc.
    Good examples: "Management Changes", "Financial Performance", "Strategic Options"
    Bad examples: "And Power has Shifted", "The Company Background", "But There are Issues"
    
    Think like organizing major talking points for a 5-minute investment pitch - you want substantial sections, not tiny fragments.
    
    Original text:
    {text}
    """
    
    try:
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

def launch_space_visualization(sections: list, company_name: str = "INVESTMENT"):
    """
    Create and launch the cinematic brain visualization - SIMPLE DOWNLOAD
    """
    # Create the HTML content for the brain visualization
    html_content = create_space_visualization_html(sections, company_name)
    
    st.markdown("---")
    st.markdown("### 🧠 Brain Visualization Ready!")
    
    # Simple download button
    st.download_button(
        label="⬇️ Download Brain Visualization File",
        data=html_content,
        file_name=f"{company_name}_brain_visualization.html",
        mime="text/html",
        type="primary"
    )
    
    st.markdown("""
    ### How to Open:
    1. **Click the download button above**
    2. **Go to your Downloads folder** 
    3. **Double-click the HTML file** to open it in your browser
    4. **Enjoy the full-screen brain visualization!**
    
    *(The file will work on any computer - just double-click to open)*
    """)
    
    # Also provide the raw HTML for copying if needed
    with st.expander("🔧 Advanced: Copy HTML Code"):
        st.code(html_content, language="html")
        st.markdown("*Copy this code and save it as a .html file if the download doesn't work*")

def create_space_visualization_html(sections: list, company_name: str = "INVESTMENT") -> str:
    """
    Create a professional brain-centered investment thesis visualization
    """
    # Convert sections to JSON safely
    sections_json = json.dumps(sections)
    
    # Create concise summaries for each section using AI
    def create_bullet_points(title, content):
        """Use AI to extract 3 key bullet points from content"""
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Truncate content if too long to avoid API issues
            max_content_length = 1000  # Shorter for speed
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            prompt = f"""
            Analyze this investment thesis section and extract exactly 3 key bullet points.
            
            Section: {title}
            Content: {content}
            
            Create 3 bullet points that are:
            - 5-8 words each
            - Key takeaways for investors
            - Complete thoughts (no fragments)
            - Specific insights from the content above
            
            Format: Return only 3 lines, no bullets or numbers, just the text.
            
            Example good outputs:
            Stock down 80% creates opportunity
            New CEO has transaction experience  
            Activists pushing for strategic alternatives
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100,  # Smaller for speed
                timeout=8
            )
            
            result = response.choices[0].message.content.strip()
            
            if not result:
                raise Exception("Empty response from AI")
            
            bullets = [line.strip() for line in result.split('\n') if line.strip()]
            
            # Validate we got reasonable bullets
            if len(bullets) < 2:
                raise Exception("Not enough bullets generated")
            
            # Filter out any bullets that are too generic or contain fallback phrases
            filtered_bullets = []
            generic_phrases = ['key thesis point', 'investment consideration', 'strategic factor', 'requires analysis']
            
            for bullet in bullets:
                is_generic = any(phrase in bullet.lower() for phrase in generic_phrases)
                if not is_generic and len(bullet.split()) >= 3:
                    filtered_bullets.append(bullet)
            
            # If we don't have enough good bullets, try a simpler approach
            if len(filtered_bullets) < 2:
                # Extract key phrases from the content directly
                sentences = content.replace('\n', '. ').split('.')
                extracted_bullets = []
                
                for sentence in sentences[:10]:  # Look at first 10 sentences
                    sentence = sentence.strip()
                    if len(sentence.split()) >= 5 and len(sentence.split()) <= 12:
                        # Look for sentences with investment-relevant keywords
                        keywords = ['CEO', 'stock', 'price', 'margin', 'revenue', 'activist', 'M&A', 'sale', 'acquisition', 'value', 'growth', 'decline']
                        if any(keyword.lower() in sentence.lower() for keyword in keywords):
                            extracted_bullets.append(sentence)
                            if len(extracted_bullets) >= 3:
                                break
                
                if extracted_bullets:
                    return extracted_bullets[:3]
            
            # Ensure we have exactly 3 bullets
            while len(filtered_bullets) < 3:
                if content:
                    # Try to extract a simple fact from content
                    words = content.split()
                    if len(words) > 6:
                        simple_bullet = ' '.join(words[:6])
                        filtered_bullets.append(simple_bullet)
                    else:
                        filtered_bullets.append(f"{title} under analysis")
                else:
                    filtered_bullets.append(f"{title} key factors")
                    
            return filtered_bullets[:3]
            
        except Exception as e:
            print(f"AI bullet generation failed for {title}: {str(e)}")
            
            # Better fallback - extract from actual content
            if content:
                sentences = content.replace('\n', '. ').split('.')
                fallback_bullets = []
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and len(sentence.split()) >= 4 and len(sentence.split()) <= 10:
                        fallback_bullets.append(sentence)
                        if len(fallback_bullets) >= 3:
                            break
                
                if fallback_bullets:
                    return fallback_bullets[:3]
            
            # Last resort fallback
            return [
                f"{title} presents opportunity",
                f"Key metrics show potential",
                f"Investment thesis under review"
            ]
    
    # Process sections for concise display
    processed_sections = []
    for section in sections:
        processed_sections.append({
            'title': section['title'],
            'bullets': create_bullet_points(section['title'], section['content'])
        })
    
    processed_json = json.dumps(processed_sections)
    
    # Create HTML template with Randy's modifications
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
            overflow: hidden;
            font-family: 'Inter', sans-serif;
            cursor: default;
            height: 100vh;
            position: relative;
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
                radial-gradient(1px 1px at 90px 40px, rgba(236, 72, 153, 0.3), transparent),
                radial-gradient(1px 1px at 130px 80px, rgba(79, 70, 229, 0.2), transparent),
                radial-gradient(2px 2px at 160px 30px, rgba(124, 58, 237, 0.1), transparent);
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
            width: 100vw;
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
            top: 60px;
            left: 50%;
            transform: translateX(-50%);
            color: #ffffff;
            font-size: 42px;
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
            top: 110px;
            left: 50%;
            transform: translateX(-50%);
            color: rgba(255, 255, 255, 0.7);
            font-size: 18px;
            font-weight: 400;
            letter-spacing: 0.5px;
            text-align: center;
        }
        
        /* Thesis sections positioned around center - BIGGER BOXES */
        .thesis-section {
            position: absolute;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 24px 28px;
            min-width: 240px;
            max-width: 300px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        
        .thesis-section:hover {
            background: rgba(79, 70, 229, 0.2);
            border-color: rgba(79, 70, 229, 0.5);
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(79, 70, 229, 0.3);
        }
        
        .thesis-section h3 {
            color: #ffffff;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            text-align: center;
            letter-spacing: 0.3px;
        }
        
        .thesis-preview {
            color: rgba(255, 255, 255, 0.8);
            font-size: 13px;
            font-weight: 400;
            text-align: center;
            line-height: 1.4;
        }
        
        /* Blur overlay for background */
        .blur-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            backdrop-filter: blur(8px);
            z-index: 500;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .blur-overlay.active {
            opacity: 1;
            visibility: visible;
        }
        
        /* Content popup - REPLACES the clicked box */
        .content-popup {
            position: fixed !important;
            background: linear-gradient(135deg, rgba(15, 15, 35, 0.95), rgba(26, 26, 46, 0.95));
            border: 1px solid rgba(79, 70, 229, 0.3);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(20px);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transform: scale(0.8);
            transition: all 0.3s ease;
        }
        
        .content-popup.active {
            opacity: 1;
            visibility: visible;
            transform: scale(1);
        }
        
        .popup-title {
            color: #ffffff;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 12px;
            text-align: center;
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .popup-bullets {
            list-style: none;
            padding: 0;
        }
        
        .popup-bullets li {
            color: #e0e7ff;
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 8px;
            padding-left: 18px;
            position: relative;
            line-height: 1.3;
        }
        
        .popup-bullets li::before {
            content: '→';
            position: absolute;
            left: 0;
            color: #4f46e5;
            font-weight: 700;
            font-size: 14px;
        }
        
        .close-btn {
            position: absolute;
            top: 5px;
            right: 8px;
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.7);
            font-size: 18px;
            cursor: pointer;
            transition: color 0.3s ease;
            line-height: 1;
        }
        
        .close-btn:hover {
            color: #ffffff;
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
                <div style="width: 50px; height: 50px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: auto; margin-top: 75px;"></div>
            </div>
        </div>
    </div>
    
    <div class="blur-overlay" id="blur-overlay"></div>
    
    <div class="content-popup" id="content-popup">
        <button class="close-btn">×</button>
        <div class="popup-title"></div>
        <ul class="popup-bullets"></ul>
    </div>

    <script>
        const thesisSections = SECTIONS_JSON_PLACEHOLDER;
        
        // Position sections around the center - BIGGER SPACING
        const positions = [
            { top: '18%', left: '15%' },
            { top: '18%', right: '15%' },
            { top: '45%', left: '8%' },
            { top: '45%', right: '8%' },
            { top: '72%', left: '15%' },
            { top: '72%', right: '15%' }
        ];
        
        function createThesisLayout() {
            const container = document.getElementById('container');
            
            thesisSections.forEach((section, index) => {
                if (index >= positions.length) return;
                
                // Create section element
                const sectionEl = document.createElement('div');
                sectionEl.className = 'thesis-section';
                sectionEl.style.position = 'absolute';
                sectionEl.dataset.index = index;
                
                // Apply position
                const pos = positions[index];
                Object.keys(pos).forEach(key => {
                    sectionEl.style[key] = pos[key];
                });
                
                // Add content
                sectionEl.innerHTML = `
                    <h3>${section.title}</h3>
                    <div class="thesis-preview">Click to explore insights</div>
                `;
                
                // Add click handler
                sectionEl.addEventListener('click', (e) => {
                    showSectionDetails(section, sectionEl);
                });
                
                container.appendChild(sectionEl);
            });
        }
        
        function showSectionDetails(section, clickedElement) {
            const popup = document.getElementById('content-popup');
            const blurOverlay = document.getElementById('blur-overlay');
            const title = popup.querySelector('.popup-title');
            const bullets = popup.querySelector('.popup-bullets');
            
            // Set content
            title.textContent = section.title;
            bullets.innerHTML = '';
            section.bullets.forEach(bullet => {
                const li = document.createElement('li');
                li.textContent = bullet;
                bullets.appendChild(li);
            });
            
            // Get clicked box position - EXACT same position
            const boxRect = clickedElement.getBoundingClientRect();
            
            // Position popup EXACTLY where the box is (replace it)
            popup.style.position = 'fixed';
            popup.style.left = boxRect.left + 'px';
            popup.style.top = boxRect.top + 'px';
            popup.style.width = boxRect.width + 'px';
            popup.style.minWidth = boxRect.width + 'px';
            
            // Show popup and blur everything else
            blurOverlay.classList.add('active');
            popup.classList.add('active');
        }
        
        function closePopup() {
            document.getElementById('content-popup').classList.remove('active');
            document.getElementById('blur-overlay').classList.remove('active');
        }
        
        // Event listeners
        document.querySelector('.close-btn').addEventListener('click', closePopup);
        document.getElementById('blur-overlay').addEventListener('click', closePopup);
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closePopup();
            }
        });
        
        // Initialize
        createThesisLayout();
    </script>
</body>
</html>'''
    
    # Replace placeholders safely
    html_content = html_template.replace('SECTIONS_JSON_PLACEHOLDER', processed_json)
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
        # View visualization button - NOW SHOWS IN APP!
        has_formatted_text = st.session_state.current_text and ":" in st.session_state.current_text
        viz_button = st.button("🧠 Launch Brain Visualization", type="secondary", disabled=not has_formatted_text)
        
        if viz_button:
            # Use stored company name if available, otherwise extract from current text
            if hasattr(st.session_state, 'company_name'):
                stored_company = st.session_state.company_name
            else:
                stored_company = extract_company_name(st.session_state.current_text)
            
            # Parse the thesis sections for the visualization
            sections = parse_thesis_sections(st.session_state.current_text)
            launch_space_visualization(sections, stored_company)
    
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
    
    # Show tip only if text has been formatted AND we didn't just format it
    if (st.session_state.current_text and ":" in st.session_state.current_text and 
        not st.session_state.just_formatted):
        st.info("💡 **Tip:** Your thesis has been formatted with clear section headers. You can still edit the text above if needed.")
    
    # Reset the just_formatted flag after showing success
    if st.session_state.just_formatted:
        st.session_state.just_formatted = False

if __name__ == "__main__":
    main()
