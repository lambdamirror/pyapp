
from datetime import datetime, timedelta
import requests
from config.settings import *
from utils.logger import logger

class PaypalClient():
    def __new__(cls):
        """
        The __new__ method is called before __init__, so we can use it to return an already created
        instance
        
        :param cls: The class that is being instantiated
        :return: The instance of the class.
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(PaypalClient, cls).__new__(cls)
        return cls.instance
    
    def _headers(self):
        """
        It returns a dictionary with two keys, `Content-Type` and `Authorization`, and the values are
        `application/json` and `Bearer <access_token>`, respectively.
        :return: A dictionary with the key 'Content-Type' and the value 'application/json' and the key
        'Authorization' and the value 'Bearer {self.access_token}'
        """
        if (self.access_token is None) or (self.expired_time < datetime.utcnow() + timedelta(hours=1)): 
            self.connect()
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

    def __init__(self) -> None:
        """
        > The `__init__` function is called when the class is instantiated
        """
        self.root_url = f"https://api-m{'.sandbox' if API_ENV != 'prod' else ''}.paypal.com"
        self.connect()

    def connect(self):
        """
        It uses the `requests` library to make a POST request to the PayPal API, and then it stores the
        access token in the `access_token` attribute of the `PayPal` object
        """
        with requests.Session() as session:
            session.auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
            r = session.post(f"{self.root_url}/v1/oauth2/token", data={'grant_type': 'client_credentials'})
            data = r.json()
            self.expired_time = datetime.utcnow() + timedelta(seconds=data.get('expires_in'))
            self.access_token = r.json().get('access_token')
        logger.info(f"[Paypal API] Connect to {self.root_url} token expired at {self.expired_time.strftime(FULL_DATE_STR_FORMAT)}")


    def get_payment_capture(self, order_id: str):
        """
        It captures the payment for the order.
        
        :param order_id: The order ID that you received from the create_order call
        :type order_id: str
        :return: The response is a JSON object that contains the status of the payment.
        """
        url = f"{self.root_url}/v2/checkout/orders/{order_id}/capture"
        r = requests.request("POST", url, headers=self._headers(), data={})
        return r.json()

    def get_order(self, order_id: str):
        """
        It makes a GET request to the PayPal API to get the order details for the order with the given ID
        
        :param order_id: The order ID of the order you want to get
        :type order_id: str
        :return: A JSON object containing the order details.
        """
        url = f"{self.root_url}/v2/checkout/orders/{order_id}"
        r = requests.request("GET", url, headers=self._headers(), data={})
        return r.json()

paypal_client = PaypalClient()