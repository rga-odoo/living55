{
    # Application Information
    'name': 'Product Dimension ERPify',
    'version': '14.0.0',
    'category': 'Product',
    'description': """ 
        Product Dimension ERPify
    """,
    'summary': """
        Product Dimension ERPify
    """,

    # Author Information
    'author': 'ERPify Inc.',
    'maintainer': 'ERPify Inc',
    'website': 'erpify.biz',

    # Technical Information
    'depends': ['product'],
    'data': [
        'views/product_view.xml'
    ],

    # App Technical Information
    'installable': True,
    'auto_install': False,
    'application': True,
    'active': True,
    'support': 'az@erpify.biz',
}
