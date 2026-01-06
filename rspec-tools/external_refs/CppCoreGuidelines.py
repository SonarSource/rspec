import requests
import re

def download_cpp_core_guidelines():
    """
    Downloads the CppCoreGuidelines.md file from the official GitHub repository.
    """
    referenceHash = "e49158a"  # Specific commit hash
    documentUrl = f"https://raw.githubusercontent.com/isocpp/CppCoreGuidelines/{referenceHash}/CppCoreGuidelines.md"
    link_url = f"https://github.com/isocpp/CppCoreGuidelines/blob/{referenceHash}/CppCoreGuidelines.md"
    try:
        response = requests.get(documentUrl)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Extract guidelines (3rd level titles starting with ###)
        guidelines = re.findall(r'^### (.+)$', response.text, re.MULTILINE)
        
        print(f"Found {len(guidelines)} guidelines:")
        with open('external_refs/CppCoreGuidelines.adoc', 'w', encoding='utf-8') as f:
            for guideline in guidelines:
                # Parse the guideline header to extract anchor, ID, and title
                # Format: <a name="Rxxx-yyyy"></a>R.1: Some title
                match = re.match(r'(?:<a name="([^"]+)"></a>)?([^:]+):\s*(.+)$', guideline)
                            
                if match:
                    guideline_anchor = match.group(2) + ": " + match.group(3)
                    guideline_anchor = ''.join(c.lower() if c.isalnum() else '-' if c == ' ' else '' for c in guideline_anchor)
                    guideline_id = match.group(2)
                    guideline_title = match.group(3)
                else:
                    print(f"Could not parse guideline: {guideline}")
                    continue
    
                # Only keep the 'real' guidelines
                if not re.search(r'\d$', guideline_id) or re.search(r'^FAQ', guideline_id):
                    continue
                attribute_guideline_id = guideline_id.replace('.', '_')
                # Collect guideline info
                f.write(f":ccg_{attribute_guideline_id}: pass:quotes[C++ Core Guidelines - {link_url}#{guideline_anchor}[{guideline_id}: {guideline_title}]]\n")
        
        print("Successfully downloaded CppCoreGuidelines.md")
        return response.text
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None

if __name__ == "__main__":
    download_cpp_core_guidelines()