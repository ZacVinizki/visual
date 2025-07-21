import streamlit as st
from openai import OpenAI
import os
import tempfile
import webbrowser
import json
import re
import streamlit.components.v1 as components

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
    Create and launch the cinematic brain visualization - NOW SHOWS IN APP!
    """
    # Create the HTML content for the brain visualization
    html_content = create_space_visualization_html(sections, company_name)
    
    # Show directly in Streamlit instead of opening browser
    st.markdown("---")
    st.markdown("### 🧠 Interactive Investment Analysis")
    st.markdown("*Click on any section around the brain to explore key insights*")
    
    # Display the visualization directly in the app
    components.html(html_content, height=700, scrolling=False)
    
    # Also provide download option for full-screen experience
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
    
    # Create HTML template
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
        
        /* Central brain container */
        #brain-container {
            position: relative;
            width: 200px;
            height: 200px;
            margin: 0 auto;
        }
        
        #brain {
            width: 200px;
            height: 200px;
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
            font-size: 48px;
            font-weight: 300;
        }
        
        /* Thesis sections positioned around brain */
        .thesis-section {
            position: absolute;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 20px 24px;
            min-width: 200px;
            max-width: 250px;
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
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            text-align: center;
            letter-spacing: 0.3px;
        }
        
        .thesis-preview {
            color: rgba(255, 255, 255, 0.8);
            font-size: 12px;
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
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 90%;
            position: relative;
            backdrop-filter: blur(20px);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        }
        
        .modal-title {
            color: #ffffff;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 30px;
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
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 16px;
            padding-left: 30px;
            position: relative;
            line-height: 1.5;
        }
        
        .modal-bullets li::before {
            content: '→';
            position: absolute;
            left: 0;
            color: #4f46e5;
            font-weight: 700;
            font-size: 20px;
        }
        
        .close-btn {
            position: absolute;
            top: 15px;
            right: 20px;
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.7);
            font-size: 28px;
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
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            color: rgba(255, 255, 255, 0.6);
            font-size: 14px;
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
        const companyName = "COMPANY_NAME_PLACEHOLDER";
        
        // Position sections around the brain
        const positions = [
            { top: '20%', left: '15%', lineAngle: 135 },
            { top: '20%', right: '15%', lineAngle: 45 },
            { top: '50%', left: '8%', lineAngle: 180 },
            { top: '50%', right: '8%', lineAngle: 0 },
            { top: '75%', left: '15%', lineAngle: 225 },
            { top: '75%', right: '15%', lineAngle: 315 }
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
                    <div class="thesis-preview">Click to explore key insights</div>
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
            
            // Calculate line position and rotation based on section position
            const centerX = window.innerWidth / 2;
            const centerY = window.innerHeight / 2;
            
            let startX = centerX;
            let startY = centerY;
            let length = 150;
            let angle = position.lineAngle || 0;
            
            line.style.width = length + 'px';
            line.style.left = (startX - length / 2) + 'px';
            line.style.top = startY + 'px';
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
