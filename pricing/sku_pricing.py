# Annual per-seat list price in USD for common Microsoft 365 SKUs.
# Source: approximate Microsoft public list pricing (2024).
# Unknown SKUs are priced at $0.0 — use dict.get(sku, 0.0).
SKU_PRICING: dict[str, float] = {
    "SPE_E3": 360.00,                 # Microsoft 365 E3
    "SPE_E5": 576.00,                 # Microsoft 365 E5
    "ENTERPRISEPACK": 240.00,          # Office 365 E3
    "ENTERPRISEPREMIUM": 408.00,       # Office 365 E5
    "O365_BUSINESS_PREMIUM": 150.00,   # Microsoft 365 Business Premium
    "SMB_BUSINESS": 72.00,             # Microsoft 365 Business Basic
    "SMB_BUSINESS_PREMIUM": 150.00,    # Microsoft 365 Business Standard
    "FLOW_FREE": 0.00,
    "POWER_BI_STANDARD": 0.00,
    "POWER_BI_PRO": 120.00,
    "PROJECTPREMIUM": 660.00,          # Project Plan 5
    "PROJECTPROFESSIONAL": 480.00,     # Project Plan 3
    "VISIOONLINE_PLAN1": 60.00,        # Visio Plan 1
    "VISIOCLIENT": 270.00,             # Visio Plan 2
    "TEAMS_EXPLORATORY": 0.00,
    "MCOSTANDARD": 48.00,              # Skype for Business Online
    "AAD_PREMIUM": 72.00,              # Azure AD Premium P1
    "AAD_PREMIUM_P2": 108.00,          # Azure AD Premium P2
    "EMS": 252.00,                     # Enterprise Mobility + Security E3
    "EMSPREMIUM": 432.00,              # Enterprise Mobility + Security E5
    "INTUNE_A": 96.00,                 # Microsoft Intune
    "ATP_ENTERPRISE": 60.00,           # Defender for Office 365 Plan 1
    "THREAT_INTELLIGENCE": 108.00,     # Defender for Office 365 Plan 2
    "WIN10_PRO_ENT_SUB": 168.00,       # Windows 10/11 Enterprise E3
    "WIN_ENT_E5": 192.00,              # Windows 10/11 Enterprise E5
}
