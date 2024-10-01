import logging

import requests
from app.db.db_utils import get_db
from app.db.postgresdb import PostgresDB


class CurrencyConversionManager:
    api_base_url = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1"
    def __init__(self):
        self.db:PostgresDB = get_db()
        self.logger = logging.getLogger(__name__)
        
    def get_available_currencies(self) -> list:
        """Fetch the list of available currencies from the API."""
        try:
            response = requests.get(f"{CurrencyConversionManager.api_base_url}/currencies.json")
            if response.status_code == 200:
                return list(response.json().keys())
            else:
                self.logger.error("Failed to fetch currencies from the API.")
                return []
        except Exception as e:
            self.logger.error(f"Error fetching currencies: {str(e)}", exc_info=True)
            return []

    def convert_currency(self, from_currency, to_currency, amount) -> str:
        """Convert currency from one to another."""
        try:
            from_currency = from_currency.lower()
            to_currency = to_currency.lower()
            available_currencies = self.get_available_currencies()
            if from_currency not in available_currencies or to_currency not in available_currencies:
                self.logger.error(f"Invalid currency code(s): {from_currency}, {to_currency}")
                return f"{amount} {from_currency}"
            # Base URL structure for the new API
            base_url = CurrencyConversionManager.api_base_url + f"/currencies/{from_currency}.json"
            response = requests.get(base_url)
            data = response.json()

            if response.status_code == 200 and to_currency in data[from_currency]:
                # Fetch the conversion rate for the target currency
                rate = data[from_currency].get(to_currency)
                if rate:
                    # Perform the conversion
                    converted_amount = float(rate) * amount
                    self.logger.info(f"Converted {amount} {from_currency} to {converted_amount:.2f} {to_currency}.")
                    return f"{converted_amount:.2f} {to_currency}"

            # Log error if rate not found
            self.logger.error(f"Failed to find conversion rate for {to_currency} in the API response.")
            return f"{amount} {from_currency}"
        except Exception as e:
            self.logger.error(f"Currency conversion error: {str(e)}", exc_info=True)
            return f"{amount} {from_currency}"

    def convert_budget(self, from_currency, to_currency, min_budget, max_budget) -> str:
        """Convert budget from one currency to another."""
        try:
            from_currency = from_currency.lower()
            to_currency = to_currency.lower()
            available_currencies = self.get_available_currencies()
            if from_currency not in available_currencies or to_currency not in available_currencies:
                self.logger.error(f"Invalid currency code(s): {from_currency}, {to_currency}")
                return f"{min_budget}-{max_budget} {from_currency}"
            # Base URL structure for the new API
            base_url = CurrencyConversionManager.api_base_url + f"/currencies/{from_currency}.json"
            
            response = requests.get(base_url)
            data = response.json()

            if response.status_code == 200 and to_currency in data[from_currency]:
                # Fetch the conversion rate for the target currency
                rate = data[from_currency].get(to_currency)
                if rate:
                    # Perform the conversion
                    converted_min = float(rate) * min_budget
                    converted_max = float(rate) * max_budget
                    self.logger.info(f"Converted {min_budget}-{max_budget} {from_currency} to {converted_min:.2f}-{converted_max:.2f} {to_currency}.")
                    return f"{converted_min:.2f}-{converted_max:.2f} {to_currency}"

            # Log error if rate not found
            self.logger.error(f"Failed to find conversion rate for {to_currency} in the API response.")
            return f"{min_budget}-{max_budget} {from_currency}"  # Fallback to original values

        except Exception as e:
            self.logger.error(f"Currency conversion error: {str(e)}", exc_info=True)
            return f"{min_budget}-{max_budget} {from_currency}"  # Fallback in case of error
                
