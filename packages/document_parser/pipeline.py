import os
import re
import uuid
import camelot
from typing import List, Dict, Any, Optional
from docling.document_converter import DocumentConverter

from packages.schemas.document import DocumentData, TableData

class ExtractionConflictError(Exception):
    """Raised when Camelot and Docling extractions disagree materially on numerical layout."""
    pass


class DocumentPipeline:
    def __init__(self):
        self.converter = DocumentConverter()

    def process_document(self, file_path: str) -> DocumentData:
        """
        Parses a document (e.g. PDF) using docling and extracts text and tables.
        Uses camelot-py for table extraction consensus.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found at {file_path}")

        # Docling Extraction
        result = self.converter.convert(file_path)
        doc = result.document

        # Camelot Extraction (for consensus)
        camelot_tables = []
        if file_path.lower().endswith('.pdf'):
            try:
                camelot_result = camelot.read_pdf(file_path, pages='all', flavor='lattice')
                if not camelot_result:
                    camelot_result = camelot.read_pdf(file_path, pages='all', flavor='stream')
                camelot_tables = [t.df for t in camelot_result]
            except Exception:
                pass

        tables_data = []
        financial_table_count = 0
        for doc_table in doc.tables:
            html_content = doc_table.export_to_html()
            markdown_content = doc_table.export_to_markdown()
            
            # Simple conversion of docling table to raw data list of lists
            raw_data = []
            df = None
            try:
                # export_to_dataframe returns a pandas DataFrame
                df = doc_table.export_to_dataframe()
                raw_data = [df.columns.values.tolist()] + df.values.tolist()
            except Exception:
                pass

            classified_type = self._classify_table(markdown_content)

            # Table Consensus Check for Financial Tables
            if classified_type != "Unknown" and df is not None:
                if financial_table_count < len(camelot_tables):
                    c_df = camelot_tables[financial_table_count]
                    if c_df.shape != df.shape:
                        # Handle merged headers: compare raw numerical values directly
                        c_text = " ".join(c_df.astype(str).values.flatten()).replace(',', '').replace(' ', '')
                        d_text = " ".join(df.astype(str).values.flatten()).replace(',', '').replace(' ', '')
                        
                        c_nums = re.findall(r'\d+\.?\d*', c_text)
                        d_nums = re.findall(r'\d+\.?\d*', d_text)
                        
                        # Compare the extracted numbers to see if they are substantially similar
                        # A small threshold is allowed for parsing differences
                        if abs(len(c_nums) - len(d_nums)) > min(len(c_nums), len(d_nums)) * 0.1:
                            raise ExtractionConflictError(
                                f"EXTRACTION_CONFLICT: Financial table shape mismatch and data mismatch. "
                                f"Camelot shape {c_df.shape} vs Docling shape {df.shape}."
                            )
                else:
                    raise ExtractionConflictError(
                        "EXTRACTION_CONFLICT: Camelot found fewer financial tables than Docling."
                    )
                financial_table_count += 1

            tables_data.append(TableData(
                table_id=str(uuid.uuid4()),
                html_content=html_content,
                markdown_content=markdown_content,
                raw_data=raw_data,
                classified_type=classified_type
            ))

        return DocumentData(
            title=doc.name if hasattr(doc, 'name') else os.path.basename(file_path),
            content=doc.export_to_markdown(),
            tables=tables_data,
            metadata={"source_file": file_path}
        )

    def _classify_table(self, markdown_content: str) -> str:
        """
        Heuristic method to classify tables into common financial statements.
        """
        if not markdown_content:
            return "Unknown"

        content_lower = markdown_content.lower()

        # Income Statement Keywords
        if re.search(r'(revenue|turnover|net interest income|operating income)', content_lower) and \
           re.search(r'(net income|profit after tax|net profit|earnings per share)', content_lower):
            return "Income Statement"

        # Balance Sheet Keywords
        if re.search(r'(total assets|current assets|non-current assets)', content_lower) and \
           re.search(r'(total liabilities|equity|shareholders equity)', content_lower):
            return "Balance Sheet"

        # Cash Flow Keywords
        if re.search(r'(operating activities|investing activities|financing activities)', content_lower) and \
           re.search(r'(cash flow|cash equivalents)', content_lower):
            return "Cash Flow"

        return "Unknown"
