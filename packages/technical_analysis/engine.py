import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from decimal import Decimal
from .schemas import (
    DataQualityReport,
    LiquidityProfile,
    IndicatorResult,
    MACDResult,
    BollingerBandsResult,
    TechnicalRegime
)

class TechnicalAnalysisEngine:
    def __init__(self, data: pd.DataFrame):
        """
        Expects a pandas DataFrame with columns:
        ['date', 'open', 'high', 'low', 'close', 'volume']
        Ordered by date ascending.
        """
        self.data = data.copy()
        if not self.data.empty:
            self.data.sort_values(by='date', inplace=True)
            self.data.reset_index(drop=True, inplace=True)

    def check_data_quality(self, min_periods: int = 20) -> DataQualityReport:
        if len(self.data) < min_periods:
            return DataQualityReport(
                is_valid=False,
                status="INSUFFICIENT_DATA",
                missing_days=min_periods - len(self.data),
                zero_volume_days=0,
                stale_price_days=0,
                reason=f"Data length {len(self.data)} is less than required {min_periods}"
            )
            
        zero_vol_days = int((self.data['volume'] == 0).sum())
        
        # Stale prices: close price doesn't change from previous day (and volume is 0 or low)
        stale_mask = (self.data['close'] == self.data['close'].shift(1))
        stale_days = int(stale_mask.sum())
        
        is_valid = len(self.data) >= min_periods
        
        return DataQualityReport(
            is_valid=is_valid,
            status="OK" if is_valid else "POOR_QUALITY",
            missing_days=0,
            zero_volume_days=zero_vol_days,
            stale_price_days=stale_days,
            reason=None if is_valid else "Too many stale prices"
        )

    def assess_liquidity(self, period: int = 30) -> LiquidityProfile:
        if len(self.data) < period:
            return LiquidityProfile(
                average_daily_volume=0.0,
                zero_volume_frequency=1.0,
                is_illiquid=True,
                status="INSUFFICIENT_DATA"
            )
            
        recent = self.data.tail(period)
        avg_vol = float(recent['volume'].mean())
        zero_vol_freq = float((recent['volume'] == 0).sum() / period)
        
        is_illiquid = zero_vol_freq > 0.3 or avg_vol < 1000  # Thresholds for African markets
        
        return LiquidityProfile(
            average_daily_volume=avg_vol,
            zero_volume_frequency=zero_vol_freq,
            is_illiquid=is_illiquid,
            status="ILLIQUID" if is_illiquid else "LIQUID"
        )

    def calculate_sma(self, period: int) -> IndicatorResult:
        if len(self.data) < period:
            return IndicatorResult(value=None, status="INSUFFICIENT_DATA", reason=f"Need {period} periods")
        val = self.data['close'].rolling(window=period).mean().iloc[-1]
        return IndicatorResult(value=float(val), status="OK")

    def calculate_ema(self, period: int) -> IndicatorResult:
        if len(self.data) < period:
            return IndicatorResult(value=None, status="INSUFFICIENT_DATA", reason=f"Need {period} periods")
        val = self.data['close'].ewm(span=period, adjust=False).mean().iloc[-1]
        return IndicatorResult(value=float(val), status="OK")

    def calculate_rsi(self, period: int = 14) -> IndicatorResult:
        if len(self.data) < period + 1:
            return IndicatorResult(value=None, status="INSUFFICIENT_DATA", reason=f"Need {period+1} periods")
        
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        val = rsi.iloc[-1]
        if np.isnan(val) or np.isinf(val):
            val = 100.0 if avg_loss.iloc[-1] == 0 and avg_gain.iloc[-1] > 0 else 50.0
            
        return IndicatorResult(value=float(val), status="OK")

    def calculate_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> MACDResult:
        if len(self.data) < slow + signal:
            return MACDResult(macd=None, signal=None, histogram=None, status="INSUFFICIENT_DATA")
            
        ema_fast = self.data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.data['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return MACDResult(
            macd=float(macd_line.iloc[-1]),
            signal=float(signal_line.iloc[-1]),
            histogram=float(histogram.iloc[-1]),
            status="OK"
        )
        
    def calculate_bollinger_bands(self, period: int = 20, num_std: float = 2.0) -> BollingerBandsResult:
        if len(self.data) < period:
            return BollingerBandsResult(upper=None, middle=None, lower=None, status="INSUFFICIENT_DATA")
            
        sma = self.data['close'].rolling(window=period).mean()
        std = self.data['close'].rolling(window=period).std()
        
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        
        return BollingerBandsResult(
            upper=float(upper.iloc[-1]),
            middle=float(sma.iloc[-1]),
            lower=float(lower.iloc[-1]),
            status="OK"
        )

    def determine_regime(self) -> TechnicalRegime:
        sma50_res = self.calculate_sma(50)
        sma200_res = self.calculate_sma(200)
        rsi_res = self.calculate_rsi(14)
        bb_res = self.calculate_bollinger_bands(20)
        
        explanation = {}
        
        # Trend
        if sma50_res.status == "OK" and sma200_res.status == "OK":
            if sma50_res.value > sma200_res.value:
                trend = "Bullish"
                explanation['trend'] = "SMA50 > SMA200 indicating an uptrend"
            else:
                trend = "Bearish"
                explanation['trend'] = "SMA50 <= SMA200 indicating a downtrend"
        else:
            trend = "Neutral"
            explanation['trend'] = "Insufficient data for 50/200 SMA comparison"
            
        # Momentum
        if rsi_res.status == "OK":
            if rsi_res.value > 60:
                momentum = "Bullish"
                explanation['momentum'] = f"RSI is {rsi_res.value:.2f} (>60)"
            elif rsi_res.value < 40:
                momentum = "Bearish"
                explanation['momentum'] = f"RSI is {rsi_res.value:.2f} (<40)"
            else:
                momentum = "Neutral"
                explanation['momentum'] = f"RSI is {rsi_res.value:.2f} (Neutral zone 40-60)"
        else:
            momentum = "Neutral"
            explanation['momentum'] = "Insufficient data for RSI"
            
        # Volatility
        if bb_res.status == "OK":
            width = (bb_res.upper - bb_res.lower) / bb_res.middle
            if width > 0.15:
                volatility = "High"
                explanation['volatility'] = f"Bollinger Band width is high ({width:.2%})"
            elif width < 0.05:
                volatility = "Low"
                explanation['volatility'] = f"Bollinger Band width is low ({width:.2%})"
            else:
                volatility = "Normal"
                explanation['volatility'] = f"Bollinger Band width is normal ({width:.2%})"
        else:
            volatility = "Unknown"
            explanation['volatility'] = "Insufficient data for Bollinger Bands"
            
        return TechnicalRegime(
            trend=trend,
            momentum=momentum,
            volatility=volatility,
            explanation=explanation
        )
