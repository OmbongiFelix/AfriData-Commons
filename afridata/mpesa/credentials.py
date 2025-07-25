import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64
import environ
import logging

# Initialize environment variables
env = environ.Env(
    # Set casting and default values
    DEBUG=(bool, False)
)

# Set up logging
logger = logging.getLogger(__name__)

class MpesaC2bCredential:
    consumer_key = env('MPESA_CONSUMER_KEY', default='FvFAsAmUt3KiVfuvAx0H2A8Lzg3VOS5IhyQ35ZgIBwdYVTW7')
    consumer_secret = env('MPESA_CONSUMER_SECRET', default='CYycDezeZJ2X5tYLYcG4fF9bCiFFZPyycGJGppKEY0hVaMzW2gU6FJYFzaWOcJuy')
    api_URL = env('MPESA_TOKEN_URL', default='https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials')

class MpesaAccessToken:
    @classmethod
    def get_token(cls):
        """Get M-Pesa access token with error handling"""
        try:
            r = requests.get(
                MpesaC2bCredential.api_URL,
                auth=HTTPBasicAuth(MpesaC2bCredential.consumer_key, MpesaC2bCredential.consumer_secret),
                timeout=30
            )
            r.raise_for_status()
            
            mpesa_access_token = r.json()
            validated_mpesa_access_token = mpesa_access_token.get("access_token")
            
            if not validated_mpesa_access_token:
                logger.error("No access token in response")
                raise ValueError("No access token received from M-Pesa API")
                
            logger.info("M-Pesa access token generated successfully")
            return validated_mpesa_access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting M-Pesa access token: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing M-Pesa token response: {e}")
            raise

    # For backward compatibility
    @property
    def validated_mpesa_access_token(self):
        return self.get_token()

class LipanaMpesaPpassword:
    @classmethod
    def generate_password(cls):
        """Generate M-Pesa password with current timestamp"""
        lipa_time = datetime.now().strftime('%Y%m%d%H%M%S')
        Business_short_code = env('MPESA_SHORTCODE', default="174379")
        passkey = env('MPESA_PASSKEY', default='bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
        
        data_to_encode = Business_short_code + passkey + lipa_time
        online_password = base64.b64encode(data_to_encode.encode())
        decode_password = online_password.decode('utf-8')
        
        return {
            'password': decode_password,
            'timestamp': lipa_time,
            'shortcode': Business_short_code
        }
    
    # For backward compatibility
    @property
    def lipa_time(self):
        return self.generate_password()['timestamp']
    
    @property
    def Business_short_code(self):
        return env('MPESA_SHORTCODE', default="174379")
    
    @property
    def passkey(self):
        return env('MPESA_PASSKEY', default='bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
    
    @property
    def decode_password(self):
        return self.generate_password()['password']

# Configuration class for easy access
class MpesaConfig:
    """Centralized M-Pesa configuration"""
    
    @classmethod
    def get_config(cls):
        return {
            'consumer_key': env('MPESA_CONSUMER_KEY', default='FvFAsAmUt3KiVfuvAx0H2A8Lzg3VOS5IhyQ35ZgIBwdYVTW7'),
            'consumer_secret': env('MPESA_CONSUMER_SECRET', default='CYycDezeZJ2X5tYLYcG4fF9bCiFFZPyycGJGppKEY0hVaMzW2gU6FJYFzaWOcJuy'),
            'shortcode': env('MPESA_SHORTCODE', default="174379"),
            'passkey': env('MPESA_PASSKEY', default='bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'),
            'callback_url': env('MPESA_CALLBACK_URL', default='https://your-domain.com/mpesa/callback/'),
            'token_url': env('MPESA_TOKEN_URL', default='https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'),
            'stk_push_url': env('MPESA_STK_PUSH_URL', default='https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'),
            'environment': env('MPESA_ENVIRONMENT', default='sandbox')  # sandbox or production
        }
    
    @classmethod
    def is_production(cls):
        return cls.get_config()['environment'].lower() == 'production'