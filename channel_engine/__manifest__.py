{
    # Application Information
    'name': 'Channel Engine Odoo Connector',
    'version': '14.0.0',
    'category': 'Sales',
    'description': """ 
        Channel Engine Odoo Connector to have one connection to all your channel through Odoo
    """,
    'summary': """
        
    """,

    # Author Information
    'author': 'ERPify Inc.',
    'maintainer': 'ERPify Inc',
    'website': 'erpify.biz',

    # Technical Information
    'depends': ['auto_invoice_workflow_erpify', 'delivery', 'sale', 'account', 'base', 'products_images_url_erpify'],
    'data': [
        'security/res_groups_view.xml',
        'security/ir.model.access.csv',
        'view/ce_instance_view.xml',
        'view/ce_sale_workflow_config_view.xml',
        'view/ce_product_brand_view.xml',
        'view/ce_product_product_view.xml',
        'view/ce_product_template_view.xml',
        'view/ce_log_book_view.xml',
        'view/ce_operations_view.xml',
        'view/ce_sale_order_view.xml',
        'view/ce_stock_view.xml',
        'view/ce_name.xml',
        'view/ce_config_view.xml',
        'wizard/channel_product_import_export_wizard_view.xml',
        'wizard/channel_product_wizard_view.xml',
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        'view/ce_product_images_view.xml',
    ],

    # App Technical Information
    'installable': True,
    'auto_install': False,
    'application': True,
    'active': True,
    'license': 'OPL-1',
    'price': 750,
    'currency': 'EUR',
    'support': 'az@erpify.biz',
}
