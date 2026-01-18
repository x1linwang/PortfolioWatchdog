import yfinance as yf
import numpy as np

class FinanceTools:
    @staticmethod
    def get_real_time_price(ticker):
        try:
            stock = yf.Ticker(ticker)
            return stock.fast_info['last_price']
        except:
            return 0.0

    @staticmethod
    def calculate_risk_metrics(ticker, shares):
        """Calculates metrics for a SINGLE asset."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            if hist.empty: return {"error": "No data"}
            
            # Returns & Volatility
            returns = hist['Close'].pct_change().dropna()
            current_price = stock.fast_info['last_price']
            
            # Daily Change
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                daily_return_pct = ((current_price - prev_close) / prev_close) * 100
            else:
                daily_return_pct = 0.0

            # Annual Volatility
            daily_vol = np.std(returns)
            annual_vol = daily_vol * np.sqrt(252) * 100

            # VaR (95% Confidence)
            var_95_pct = np.percentile(returns, 5) # e.g., -0.02
            
            position_value = current_price * shares
            max_loss_daily = abs(var_95_pct) * position_value

            return {
                "ticker": ticker,
                "price": round(current_price, 2),
                "position_value": round(position_value, 2),
                "daily_change_pct": round(daily_return_pct, 2),
                "volatility": round(annual_vol, 2),
                "var_95_percent": round(abs(var_95_pct) * 100, 2),
                "var_95_usd": round(max_loss_daily, 2)
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def calculate_portfolio_risk(holdings):
        """
        Aggregates risk across ALL holdings to calculate the overall portfolio risk.
        """
        total_value = 0.0
        total_var_usd = 0.0
        weighted_volatility = 0.0
        portfolio_breakdown = []

        for ticker, shares in holdings:
            # Reuses the single asset function!
            data = FinanceTools.calculate_risk_metrics(ticker, shares)
            if "error" in data: continue

            # Aggregate
            total_value += data["position_value"]
            total_var_usd += data["var_95_usd"]
            
            # Store for weighting later
            portfolio_breakdown.append(data)

        # Calculate Weighted Averages
        if total_value > 0:
            for item in portfolio_breakdown:
                weight = item["position_value"] / total_value
                weighted_volatility += item["volatility"] * weight
        
        return {
            "total_value": round(total_value, 2),
            "portfolio_var_usd": round(total_var_usd, 2), # Worst case daily loss
            "portfolio_volatility": round(weighted_volatility, 2), # Weighted Risk
            "holdings_summary": portfolio_breakdown
        }