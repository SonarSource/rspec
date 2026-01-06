import requests
import re
import os

def download_cpp_core_guidelines():
    """
    Downloads the CppCoreGuidelines.md file from the official GitHub repository.
    """
    referenceHash = "e49158a"  # Specific commit hash
    documentUrl = f"https://raw.githubusercontent.com/isocpp/CppCoreGuidelines/{referenceHash}/CppCoreGuidelines.md"
    link_url = f"https://github.com/isocpp/CppCoreGuidelines/blob/{referenceHash}/CppCoreGuidelines.md"

    # Load the local HTML file
    html_file_path = os.path.join(os.path.dirname(__file__), 'CppCoreGuidelines.html')
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    print(f"Successfully loaded {html_file_path}")

    try:
        response = requests.get(documentUrl)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Extract guidelines (3rd level titles starting with ###)
        guidelines = re.findall(r'^### (.+)$', response.text, re.MULTILINE)
        
        print(f"Found {len(guidelines)} guidelines:")
        with open('external_refs/CppCoreGuidelines.adoc', 'w', encoding='utf-8') as f:
            not_found_anchor = 0
            for guideline in guidelines:
                # Parse the guideline header to extract anchor, ID, and title
                # Format: <a name="Rxxx-yyyy"></a>R.1: Some title
                match = re.match(r'(?:<a name="([^"]+)"></a>)?([^:]+):\s(.+)$', guideline)
                            
                if match:
                    guideline_anchor = match.group(2) + ": " + match.group(3)
                    guideline_anchor = ''.join(c.lower() if (c.isalnum() or c in '_-') else '-' if c == ' ' else '' for c in guideline_anchor)
                    guideline_id = match.group(2)
                    guideline_title = match.group(3)
                else:
                    print(f"Could not parse guideline: {guideline}")
                    continue
    
                # Only keep the 'real' guidelines
                if not re.search(r'\d$', guideline_id) or re.search(r'^FAQ', guideline_id):
                    continue
                attribute_guideline_id = guideline_id.replace('.', '_')
                
                if not guideline_anchor in html_content:
                    not_found_anchor += 1
                    print(f"Warning: Anchor '{guideline_anchor}' not found in HTML content.")


                # Collect guideline info
                f.write(f":ccg_{attribute_guideline_id}: pass:quotes[C++ Core Guidelines - {link_url}#{guideline_anchor}[{guideline_id}: {guideline_title}]]\n")

            if (not_found_anchor > 0):
                print(f"Total anchors not found: {not_found_anchor}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None

if __name__ == "__main__":
    download_cpp_core_guidelines()