{
    'name': 'Automatic Workflow Settings',
    'version': '11.1',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'ERPify Inc.',
    'website': 'http://erpify.biz',
    'maintainer': 'ERPify Inc.',
    'depends': ['sale_management','account','stock','stock_account'],
    'init_xml': [],
    'data': [ 
            'view/sale_workflow_process_view.xml',
            'view/automatic_workflow_data.xml',
            'view/sale_view.xml',
            'view/transaction_log_view.xml',
            'security/ir.model.access.csv',
            'security/ir.model.access.csv',
            'view/stock_move.xml',
            'view/global_channel_ept.xml',
            'view/stock_picking.xml',
            'view/account_invoice.xml',
            'view/account_move.xml'
            
            
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

