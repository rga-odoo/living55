from datetime import datetime, timedelta
import time, json, requests

class ChannelEngine(object):
    
    def check_connection(self,instance):
        """
            This method for check connection with channel engine using order API(Using JSON).
            Order API call using PUT method.
            Example URL for Call Order(Check Connection) API:
                --> https://erpfy-dev.channelengine.net/api/v2/orders?statuses=IN_PROGRESS&api_key=xxxxxxxxxx
            @param insatnce: Current instance object.
            @return result_dict: Return response dictionary(In JSON Format) of order API.  
        """
        filter_param_path = ''
        channel_shop_url_path = instance.channel_shop_url if instance.channel_shop_url[-1]=='/' else (instance.channel_shop_url + '/')
        channel_offer_api_path = 'api/v2/orders?statuses=IN_PROGRESS&'
        channel_api_key_path = 'api_key=%s' % (instance.api_key)
        redirect_url = channel_shop_url_path + channel_offer_api_path + filter_param_path + channel_api_key_path
        headers = {"content-type": "application/json", "Accept": "application/json"}
        result_dict = requests.get(url=str(redirect_url), headers=headers)
        return result_dict.json()
    
    def get_channel_offer_api_object(self,instance, data):
        """
			This method for update product Price or Stock in channel engine using offer API(Using JSON).
			Offer API call using PUT method.
			Example URL for Call Offer(Update stock or price) API:
				--> https://erpfy-dev.channelengine.net/api/v2/offer?api_key=xxxxxxxxxx
			@param insatnce: Current instance object.
			@param data: Data inside get the product information for update.
			@return result_dict: Return response dictionary(In JSON Format) of offer API. 
        """
        channel_shop_url_path = instance.channel_shop_url if instance.channel_shop_url[-1]=='/' else (instance.channel_shop_url + '/')
        channel_offer_api_path = 'api/v2/offer?'
        channel_api_key_path = 'api_key=%s' % (instance.api_key)
        
        redirect_url = channel_shop_url_path + channel_offer_api_path + channel_api_key_path
        headers = {"content-type": "application/json", "Accept": "application/json"}
        result_dict = requests.put(url=redirect_url, data=json.dumps(data), headers=headers)
        return result_dict.json()
               
    def get_channel_product_upsert_api_object(self,instance, data):  
        """
            Example URL for Call Order API:
                --> https://erpfy-dev.channelengine.net/api/v2/products?api_key=xxxxxxxxxx
            @param insatnce: Current instance object.           
            @return result_dict: Return response dictionary(In JSON Format) of Orders API.
        """        
        channel_shop_url_path = instance.channel_shop_url if instance.channel_shop_url[-1]=='/' else (instance.channel_shop_url + '/')
        channel_products_api_path = 'api/v2/products?'
        channel_api_key_path = 'api_key=%s' % (instance.api_key)
        
        redirect_url = channel_shop_url_path + channel_products_api_path + channel_api_key_path
        headers = {"content-type": "application/json", "Accept": "application/json"}
        result_dict = requests.post(url=redirect_url, data=json.dumps(data), headers=headers)
        return result_dict.json()

    def get_channel_acknowledge_order_api_object(self, instance, data):
        """
            This method for send acknowledgement of the order from odoo to channel engine using Acknowledge API(Using JSON).
            Acknowledge API call using PUT method.
            Example URL for Call Acknowledge(Send acknowledge of order) API:
                --> https://erpfy-dev.channelengine.net/api/v2/orders/acknowledge?api_key=xxxxxxxxxx
            @param insatnce: Current instance object.
            @param data: Data inside get the order information for update.
            @return result_dict: Return response dictionary(In JSON Format) of acknowledge API. 
        """
         
        channel_shop_url_path = instance.channel_shop_url if instance.channel_shop_url[-1]=='/' else (instance.channel_shop_url + '/')
        channel_orders_api_path = 'api/v2/orders/acknowledge?'
        channel_api_key_path = 'api_key=%s' % (instance.api_key)
        
        redirect_url = channel_shop_url_path + channel_orders_api_path + channel_api_key_path
        headers = {"content-type": "application/json", "Accept": "application/json"}
        result_dict = requests.post(url=redirect_url, data=json.dumps(data), headers=headers)
        return result_dict.json()
    
  
    def get_channel_create_shipment_api_object(self, instance, data):
        """
            Example URL for Call Shipment API:
                --> https://erpfy-dev.channelengine.net/api/v2/shipments?api_key=xxxxxxxxxx
            @param insatnce: Current instance object.           
            @return result_dict: Return response dictionary(In JSON Format) of Shipment API.
            @rtype: requests.Response.json()
        """
        channel_shop_url_path = instance.channel_shop_url if instance.channel_shop_url[-1]=='/' else (instance.channel_shop_url + '/')
        channel_shipment_api_path = 'api/v2/shipments?'
        channel_api_key_path = 'api_key=%s' % (instance.api_key)
        
        redirect_url = channel_shop_url_path + channel_shipment_api_path + channel_api_key_path
        headers = {"content-type": "application/json", "Accept": "application/json"}
        result_dict = requests.post(url=redirect_url, data=json.dumps(data), headers=headers)
        return result_dict.json()


    def get_channel_order_by_filter_api_object(self, instance, filter_statuses, filter_fulfillment_type, filter_page):
        """
            This method for Import Sales Orders from channel engine using Product Orders API(JSON API).
            Product Order API call using GET method.
            Example URL for Call Get Order By Filter API:
                --> https://erpfy-dev.channelengine.net/api/v2/orders?filter.statuses=NEW&api_key=xxxxxxxxxx
            @param insatnce: Current instance object.
            @param filter_statuses: Import order status type. 
            @param filter_fulfillment_type: Filter orders on fulfillment type. This will include all orders lines, even if they are partially fulfilled by the marketplace.  To exclude orders and lines that are fulfilled by the marketplace from the response, set ExcludeMarketplaceFulfilledOrdersAndLines to true.
            @param filter_page: Import order from channel engine particular page. Default Import all page orders.
            @return result_dict: Return response dictionary(In JSON Format) of Orders API. 
            @rtype: requests.Response.json()
        """
        channel_shop_url_path = instance.channel_shop_url if instance.channel_shop_url[-1]=='/' else (instance.channel_shop_url + '/') 
        channel_order_api_path = 'api/v2/orders?'
        filter_param_path = ''
        
        for filter_status in filter_statuses:
            filter_param_path += '&filter.statuses=%s'%filter_status if filter_param_path else 'filter.statuses=%s'%filter_status
        if filter_fulfillment_type:
            filter_param_path += '&filter.fulfillmentType=%s'%filter_fulfillment_type if filter_param_path else 'filter.fulfillmentType=%s'%filter_fulfillment_type
        if filter_page:
            filter_param_path += '&filter.page=%s'%filter_page if filter_param_path else 'filter.page=%s'%filter_page
        
        channel_api_key_path = '&api_key=%s'%(instance.api_key) if filter_param_path else 'api_key=%s'%(instance.api_key)
        
        redirect_url = channel_shop_url_path + channel_order_api_path + filter_param_path + channel_api_key_path
        headers = {"content-type": "application/json", "Accept": "application/json"}
        result_dict = requests.get(url=str(redirect_url), headers=headers)
        
        return result_dict.json()
    
    def get_channel_products_object(self, instance):
        """
            This method for import channel products from channel engine using products API(Using JSON).
            Offer API call using PUT method.
            Example URL for Call Products(Get Products) API:
                --> https://erpfy-dev.channelengine.net/api/v2/products?api_key=xxxxxxxxxx
            @param instance: Current instance object.
            @return result_dict: Return response dictionary(In JSON Format) of products API. 
        """
        channel_shop_url_path = instance.channel_shop_url if instance.channel_shop_url[-1]=='/' else (instance.channel_shop_url + '/')
        channel_offer_api_path = 'api/v2/products?'
        channel_api_key_path = 'api_key=%s' % (instance.api_key)
        
        redirect_url = channel_shop_url_path + channel_offer_api_path + channel_api_key_path
        headers = {"content-type": "application/json", "Accept": "application/json"}
        result_dict = requests.get(url=redirect_url, headers=headers)
        return result_dict.json()
    
    def download_ce_order_packing_slip(self, merchant_order_no, instance):
        """
            This method for order download packing slip from channel engine using PackingSlip API(Using JSON).
            PackingSlip API call using GET method.
            Example URL for Call PackingSlip(Get Order Packing Slip) API:
                --> https://erpfy-dev.channelengine.net/api/v2/orders/MerchantOrderNumber/packingslip?api_key=xxxxxxxxxx
            @merchant_order_no: Channel order merchant number
            @param instance: Current instance object.
            @return result_dict: Return response dictionary(In JSON Format) of PackingSlip API. 
        """
        channel_shop_url_path = instance.channel_shop_url if instance.channel_shop_url[-1]=='/' else (instance.channel_shop_url + '/')
        channel_packing_slip_api_path = 'api/v2/orders/%s/packingslip?' % (merchant_order_no)
        channel_api_key_path = 'api_key=%s' % (instance.api_key)
        
        redirect_url = channel_shop_url_path + channel_packing_slip_api_path + channel_api_key_path
        headers = {"content-type": "application/json", "Accept": "application/json"}
        result_dict = requests.get(url=redirect_url, headers=headers)
        return result_dict    
    
    def get_ce_channels_api(self, instance):
        """
            This method for get list of configured channels from channel engine using Get Channels API(Using JSON).
            Get Channels call using GET method.
            Example URL for Call GetChannels(Get Channels) API:
                --> https://erpfy-dev.channelengine.net/api/v2/channels?api_key=xxxxxxxxxx
            @param instance: Current instance object.
            @return result_dict: Return response dictionary(In JSON Format) of List of Channels. 
        """
        channel_shop_url_path = instance.channel_shop_url if instance.channel_shop_url[-1]=='/' else (instance.channel_shop_url + '/')
        channel_get_channels_api_path = 'api/v2/channels?'
        channel_api_key_path = 'api_key=%s' % (instance.api_key)
        
        redirect_url = channel_shop_url_path + channel_get_channels_api_path + channel_api_key_path
        headers = {"content-type": "application/json", "Accept": "application/json"}
        result_dict = requests.get(url=redirect_url, headers=headers)
        return result_dict.json()