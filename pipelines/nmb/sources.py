"""Official NMB Bank Plc source documents.

Each entry is an annual report published on NMB's own investor relations
page. The listing page URL is stored alongside the download URL so every
extracted figure can be traced back to where the document was found.
"""

IR_LISTING_URL = (
    "https://www.nmbbank.co.tz/investor-relations-nmb/"
    "financial-and-regulatory-reports/annual-reports"
)

ANNUAL_REPORTS = {
    2025: f"{IR_LISTING_URL}?download=479:nmb-integrated-annual-report-2025",
    2024: f"{IR_LISTING_URL}?download=426:nmb-integrated-annual-report-2024",
    2023: f"{IR_LISTING_URL}?download=394:nmb-integrated-annual-report-2023",
    2022: f"{IR_LISTING_URL}?download=361:annual-report-2022",
    2021: f"{IR_LISTING_URL}?download=339:annual-report-2021",
}
