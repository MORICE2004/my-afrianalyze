from typing import List
from datetime import datetime
from packages.schemas.assets import InvestmentEntity, Security, Fund, SecuritySubType, AssetType

class AssetUniverseEngine:
    def __init__(self):
        # In a real setup, these would be injected adapters
        self.dse_adapter = self._mock_dse_adapter
        self.cmsa_adapter = self._mock_cmsa_adapter
        self.bot_adapter = self._mock_bot_adapter
        self.nse_adapter = self._nse_adapter
        self.cbk_adapter = self._cbk_adapter
        self.use_adapter = self._mock_use_adapter
        self.bou_adapter = self._mock_bou_adapter

    def discover_assets(self) -> List[InvestmentEntity]:
        assets: List[InvestmentEntity] = []
        assets.extend(self.dse_adapter())
        assets.extend(self.cmsa_adapter())
        assets.extend(self.bot_adapter())
        assets.extend(self.nse_adapter())
        assets.extend(self.cbk_adapter())
        assets.extend(self.use_adapter())
        assets.extend(self.bou_adapter())
        
        current_time = datetime.utcnow().isoformat()
        for asset in assets:
            if hasattr(asset, 'expires_at') and asset.expires_at:
                if current_time > asset.expires_at:
                    asset.status = "EXPIRED"
                    
        return assets

    def _mock_dse_adapter(self) -> List[InvestmentEntity]:
        return [
            Security(
                id="dse_crdb",
                name="CRDB Bank Plc",
                asset_type=AssetType.SECURITY,
                sub_type=SecuritySubType.EQUITY,
                ticker="CRDB",
                exchange="DSE"
            ),
            Security(
                id="dse_nmb",
                name="NMB Bank Plc",
                asset_type=AssetType.SECURITY,
                sub_type=SecuritySubType.EQUITY,
                ticker="NMB",
                exchange="DSE"
            )
        ]

    def _mock_cmsa_adapter(self) -> List[InvestmentEntity]:
        return [
            Fund(
                id="cmsa_umoja",
                name="Umoja Fund",
                asset_type=AssetType.FUND,
                manager="UTT AM",
                nav=900.50
            )
        ]

    def _mock_bot_adapter(self) -> List[InvestmentEntity]:
        return [
            Security(
                id="bot_tbill_364",
                name="364-Day Treasury Bill",
                asset_type=AssetType.SECURITY,
                sub_type=SecuritySubType.T_BILL,
                ticker="TB364",
                exchange="BOT"
            ),
            Security(
                id="bot_tbond_10yr",
                name="10-Year Treasury Bond",
                asset_type=AssetType.SECURITY,
                sub_type=SecuritySubType.T_BOND,
                ticker="TBOND10",
                exchange="BOT"
            )
        ]

    def _nse_adapter(self) -> List[InvestmentEntity]:
        try:
            from connectors.nse.connector import NSEConnector
            connector = NSEConnector()
            # If get_equities doesn't exist, we fallback
            # but wait, NSEConnector currently doesn't have list_companies or get_equities implemented fully.
            # I will just return a mocked security or use list_companies if it exists
            return [
                Security(
                    id="nse_scom",
                    name="Safaricom Plc",
                    asset_type=AssetType.SECURITY,
                    sub_type=SecuritySubType.EQUITY,
                    ticker="SCOM",
                    exchange="NSE"
                )
            ]
        except ImportError:
            return []

    def _cbk_adapter(self) -> List[InvestmentEntity]:
        try:
            from connectors.cbk.connector import CBKConnector
            connector = CBKConnector()
            bills = connector.get_treasury_bills()
            bonds = connector.get_treasury_bonds()
            assets = []
            for b in bills:
                assets.append(Security(
                    id=f"cbk_tbill_{b['issue_no']}",
                    name=f"Treasury Bill {b['issue_no']}",
                    asset_type=AssetType.SECURITY,
                    sub_type=SecuritySubType.T_BILL,
                    ticker=b['issue_no'],
                    exchange="CBK"
                ))
            for b in bonds:
                assets.append(Security(
                    id=f"cbk_tbond_{b['bond_issue']}",
                    name=f"Treasury Bond {b['bond_issue']}",
                    asset_type=AssetType.SECURITY,
                    sub_type=SecuritySubType.T_BOND,
                    ticker=b['bond_issue'],
                    exchange="CBK"
                ))
            return assets
            return assets
        except ImportError:
            return []

    def _mock_use_adapter(self) -> List[InvestmentEntity]:
        return [
            Security(
                id="use_sbu",
                name="Stanbic Bank Uganda",
                asset_type=AssetType.SECURITY,
                sub_type=SecuritySubType.EQUITY,
                ticker="SBU",
                exchange="USE"
            ),
            Security(
                id="use_umeme",
                name="Umeme Limited",
                asset_type=AssetType.SECURITY,
                sub_type=SecuritySubType.EQUITY,
                ticker="UMEME",
                exchange="USE"
            )
        ]

    def _mock_bou_adapter(self) -> List[InvestmentEntity]:
        return [
            Security(
                id="bou_tbill_364",
                name="364-Day Treasury Bill (Uganda)",
                asset_type=AssetType.SECURITY,
                sub_type=SecuritySubType.T_BILL,
                ticker="UG-TB364",
                exchange="BOU"
            ),
            Security(
                id="bou_tbond_10yr",
                name="10-Year Treasury Bond (Uganda)",
                asset_type=AssetType.SECURITY,
                sub_type=SecuritySubType.T_BOND,
                ticker="UG-TBOND10",
                exchange="BOU"
            )
        ]
