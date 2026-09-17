import os
import pytest
from unittest.mock import patch, MagicMock
from packages.schemas.document import DocumentData

try:
    from packages.document_parser.pipeline import DocumentPipeline
    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False

pytestmark = pytest.mark.skipif(
    not HAS_DOCLING or os.getenv("APP_ENV", "TEST") == "TEST",
    reason="Skipping document ingestion test in TEST environment or if docling fails to load due to DLL errors"
)

@pytest.fixture
def mock_docling_result():
    mock_doc = MagicMock()
    mock_doc.name = "test_doc.pdf"
    mock_doc.export_to_markdown.return_value = "# Test Document Content"
    
    mock_table = MagicMock()
    mock_table.export_to_html.return_value = "<table><tr><td>Revenue</td><td>100</td></tr><tr><td>Net Income</td><td>20</td></tr></table>"
    mock_table.export_to_markdown.return_value = "| Revenue | 100 |\n| Net Income | 20 |"
    
    mock_df = MagicMock()
    mock_df.columns.values.tolist.return_value = ["Metric", "Value"]
    mock_df.values.tolist.return_value = [["Revenue", "100"], ["Net Income", "20"]]
    mock_table.export_to_dataframe.return_value = mock_df
    
    mock_doc.tables = [mock_table]
    
    mock_result = MagicMock()
    mock_result.document = mock_doc
    return mock_result

def test_document_pipeline_integration():
    """
    Integration test using a real document (if available) or simply testing the pipeline
    initialization and method signature. 
    """
    if not HAS_DOCLING:
        pytest.skip("Docling dependencies not available")
        
    pipeline = DocumentPipeline()
    
    test_pdf_path = "test_nmb_document.pdf"
    with open(test_pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 dummy pdf content")
        
    try:
        with patch.object(pipeline.converter, 'convert') as mock_convert:
            
            mock_doc = MagicMock()
            mock_doc.name = "test_nmb_document.pdf"
            mock_doc.export_to_markdown.return_value = "# NMB Financials"
            
            mock_table = MagicMock()
            mock_table.export_to_html.return_value = "<table><tr><td>Net Interest Income</td></tr></table>"
            mock_table.export_to_markdown.return_value = "| Net Interest Income | 100 |\n| Net Profit | 20 |"
            
            mock_doc.tables = [mock_table]
            mock_result = MagicMock()
            mock_result.document = mock_doc
            mock_convert.return_value = mock_result
            
            result = pipeline.process_document(test_pdf_path)
            
            assert isinstance(result, DocumentData)
            assert result.title == "test_nmb_document.pdf"
            assert len(result.tables) == 1
            assert result.tables[0].classified_type == "Income Statement"
            
    finally:
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
