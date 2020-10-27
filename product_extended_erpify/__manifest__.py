{
    # Application Information
    'name': 'Product Extended ERPify',
    'version': '14.0.0',
    'category': 'Product',
    'description': """ 
        Product Extended ERPify
    """,
    'summary': """
        Product Extended ERPify
    """,

    # Author Information
    'author': 'ERPify Inc.',
    'maintainer': 'ERPify Inc',
    'website': 'erpify.biz',

    # Technical Information
    'depends': ['product'],
    'data': [
        'views/product.xml',
        'views/product_brand_view.xml',
        'security/ir.model.access.csv',
    ],

    # App Technical Information
    'installable': True,
    'auto_install': False,
    'application': True,
    'active': True,
    'support': 'az@erpify.biz',
}
