# -*- coding: utf-8 -*-
{
    'name': 'Products Images Link',
    'version': '13.0.2',
    'author': 'ERPfy',
    'website': 'www.erpfy.co',
    'summary': 'This modules generates links for product images which are available public.',
    'description': """
        This modules generates links for product images which are available public.
    """,
    'depends': [
        'base', 'website_sale', 'product',
    ],
    'data': [
        'views/product.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
