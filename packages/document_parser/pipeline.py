class DocumentIngestionPipeline:
    """
    Pipeline for discovering, downloading, and processing financial documents.
    """
    
    def discover_sources(self, company_id: str, exchange: str) -> list[str]:
        """
        Discover document source URLs for a given company and exchange.
        
        Args:
            company_id: The identifier for the company.
            exchange: The stock exchange identifier.
            
        Returns:
            List of source URLs to download.
        """
        raise NotImplementedError("discover_sources not implemented")

    def download_document(self, url: str) -> dict:
        """
        Download document from the specified URL and create a record.
        
        Args:
            url: The URL to download from.
            
        Returns:
            DocumentRecord containing the file path and metadata.
        """
        raise NotImplementedError("download_document not implemented")

    def hash_document(self, file_path: str) -> str:
        """
        Compute SHA256 hash of a file for deduplication.
        
        Args:
            file_path: Path to the downloaded file.
            
        Returns:
            SHA256 hash string.
        """
        raise NotImplementedError("hash_document not implemented")

    def parse_pdf(self, file_path: str) -> dict:
        """
        Parse a PDF file using Docling to extract structured content.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            ParsedDocument containing text, layout, and raw elements.
        """
        raise NotImplementedError("parse_pdf not implemented")

    def extract_tables(self, parsed_doc: dict) -> list[dict]:
        """
        Extract structured tables from a parsed document.
        
        Args:
            parsed_doc: The parsed document object.
            
        Returns:
            List of structured tables.
        """
        raise NotImplementedError("extract_tables not implemented")

    def extract_metadata(self, parsed_doc: dict) -> dict:
        """
        Extract metadata like date, report type, and company name from document.
        
        Args:
            parsed_doc: The parsed document object.
            
        Returns:
            Dictionary of extracted metadata.
        """
        raise NotImplementedError("extract_metadata not implemented")

    def identify_financial_statements(self, tables: list[dict]) -> list[str]:
        """
        Identify standard financial statement types from extracted tables.
        
        Args:
            tables: List of structured tables.
            
        Returns:
            List of statement types found (e.g., 'income_statement', 'balance_sheet').
        """
        raise NotImplementedError("identify_financial_statements not implemented")

    def store_evidence(self, extracted_data: dict) -> list[str]:
        """
        Store extracted facts as EvidenceRecords for traceability.
        
        Args:
            extracted_data: Dictionary of extracted facts and values.
            
        Returns:
            List of EvidenceRecord IDs.
        """
        raise NotImplementedError("store_evidence not implemented")

    def run_validation(self, evidence_records: list[dict]) -> list[dict]:
        """
        Run accounting and logic validation rules on evidence records.
        
        Args:
            evidence_records: List of evidence records to validate.
            
        Returns:
            List of ValidationResult objects.
        """
        raise NotImplementedError("run_validation not implemented")
