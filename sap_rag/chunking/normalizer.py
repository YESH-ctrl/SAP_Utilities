"""
Text normalizer for SAP-specific content structures:
- HTML/Markdown table transformation to key-value representations
- Preservation of Notes/Warnings/Caution markers
- Preservation of procedures and lists
- Preservation of SAP technical objects, T-Codes, and config paths
"""

import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

class TextNormalizer:
    """
    Normalizes and transforms SAP document sections for optimal retrieval quality.
    """

    @classmethod
    def convert_table_to_text(cls, html_or_md_table: str, title: Optional[str] = None) -> str:
        """
        Convert HTML or Markdown table into a retrieval-friendly key-value representation.
        """
        if not html_or_md_table or not html_or_md_table.strip():
            return ""

        # Try HTML parsing if HTML table tags present
        if "<table" in html_or_md_table.lower():
            return cls._convert_html_table(html_or_md_table, title=title)
        
        # Otherwise try Markdown table parsing
        if "|" in html_or_md_table:
            return cls._convert_markdown_table(html_or_md_table, title=title)

        return html_or_md_table.strip()

    @classmethod
    def _convert_html_table(cls, html_content: str, title: Optional[str] = None) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            return html_content.strip()

        result_blocks = []
        for tbl in tables:
            # Extract headers
            headers = []
            header_row = tbl.find("tr")
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

            rows = tbl.find_all("tr")[1:] if headers else tbl.find_all("tr")
            if not rows:
                continue

            caption = tbl.find("caption")
            table_title = title or (caption.get_text(strip=True) if caption else "Table")

            lines = [f"TABLE: {table_title}"]
            for row in rows:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if not cells:
                    continue

                if headers and len(headers) == len(cells):
                    field_strs = [f"{h}: {c}" for h, c in zip(headers, cells) if c]
                    lines.append(" | ".join(field_strs))
                else:
                    lines.append(" | ".join([c for c in cells if c]))

            result_blocks.append("\n".join(lines))

        return "\n\n".join(result_blocks)

    @classmethod
    def _convert_markdown_table(cls, md_content: str, title: Optional[str] = None) -> str:
        lines = [l.strip() for l in md_content.splitlines() if l.strip()]
        table_lines = [l for l in lines if l.startswith("|") and l.endswith("|")]
        if len(table_lines) < 2:
            return md_content.strip()

        # Extract headers from first row
        headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
        
        # Skip separator row (e.g., |---|---|)
        data_rows = []
        for l in table_lines[1:]:
            cleaned = l.strip("|")
            if re.match(r"^[\s\-:]+$", cleaned.replace("|", "")):
                continue
            cols = [c.strip() for c in cleaned.split("|")]
            data_rows.append(cols)

        table_title = title or "Table Data"
        result_lines = [f"TABLE: {table_title}"]

        for row in data_rows:
            if headers and len(headers) == len(row):
                field_strs = [f"{h}: {c}" for h, c in zip(headers, row) if c]
                result_lines.append(" | ".join(field_strs))
            else:
                result_lines.append(" | ".join([c for c in row if c]))

        return "\n".join(result_lines)

    @classmethod
    def normalize_section_content(cls, content: str) -> str:
        """
        Normalize section text:
        - Convert inline tables (HTML and Markdown)
        - Format SAP Notes / Warnings
        - Clean excess whitespace while preserving linebreaks & lists
        """
        if not content:
            return ""

        # Replace HTML tables with key-value format
        if "<table" in content.lower():
            soup = BeautifulSoup(content, "html.parser")
            for table in soup.find_all("table"):
                table_text = cls.convert_table_to_text(str(table))
                table.replace_with(soup.new_string(f"\n\n{table_text}\n\n"))
            content = str(soup)

        # Replace Markdown tables with key-value format
        if "|" in content:
            lines = content.splitlines()
            new_lines = []
            table_buffer = []

            for line in lines:
                l_strip = line.strip()
                if l_strip.startswith("|") and l_strip.endswith("|"):
                    table_buffer.append(line)
                else:
                    if table_buffer:
                        table_text = cls.convert_table_to_text("\n".join(table_buffer))
                        new_lines.append(table_text)
                        table_buffer = []
                    new_lines.append(line)

            if table_buffer:
                table_text = cls.convert_table_to_text("\n".join(table_buffer))
                new_lines.append(table_text)

            content = "\n".join(new_lines)

        # Standardize Note / Warning / Caution markers
        content = re.sub(r"(?i)\b(Note|Important|Caution|Warning|Recommendation):\s*", r"\1: ", content)

        # Clean multiple trailing spaces per line
        cleaned_lines = [line.rstrip() for line in content.splitlines()]
        
        # Collapse > 2 consecutive empty lines to 2 empty lines
        final_text = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines))

        return final_text.strip()

